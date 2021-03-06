#!/usr/bin/env python

from PIL  import Image, ImageDraw, ImageOps
from sys  import argv, stderr
from json import load
from itertools   import islice
from collections import namedtuple, defaultdict
from functools   import wraps

from colour import Color


def coroutine(func):
    @wraps(func)
    def start(*args,**kwargs):
        cr = func(*args,**kwargs)
        _ = next(cr)
        return cr
    return start


def window(iterable, size):
    it = iter(iterable)
    result = tuple(islice(it, size))
    if len(result) == size:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result


Point  = namedtuple('Point',  ['x', 'y'])
Region = namedtuple('Region', ['x', 'y', 'bbox_loc', 'bbox_shape', 'visualization'])
Frame  = namedtuple('Frame',  ['position', 'shape'])


def allocate_frames(canvas_shape, border_size):
    width, height = canvas_shape

    pad_size    = border_size // 20
    frame_size  = border_size - 2 * pad_size
    frame_shape = frame_size, frame_size

    result = defaultdict(list)
    for i in range(width // border_size):
        position = Point(pad_size + i * (pad_size + frame_size), pad_size)
        result['top'].append(Frame(position, frame_shape))

        position = Point(pad_size + i * (pad_size + frame_size),
                         (height - pad_size - frame_size)
        )
        result['bot'].append(Frame(position, frame_shape))

    for i in range((height - 2 * border_size) // border_size):
        position = Point(pad_size,
                         border_size + pad_size + (pad_size + frame_size) * i
        )
        result['left'].append(Frame(position, frame_shape))

        position = Point(width - pad_size - frame_size,
                         border_size + pad_size + (pad_size + frame_size) * i
        )
        result['right'].append(Frame(position, frame_shape))

    return result


def corners(frame):
    top_left  = frame.position
    top_right = Point(top_left.x + frame.shape[0], top_left.y)
    bot_left  = Point(top_left.x, top_left.y + frame.shape[1])
    bot_right = Point(top_left.x + frame.shape[0], top_left.y + frame.shape[1])
    return top_left, top_right, bot_left, bot_right


def nearest_frame(pos, frames):
    sq_dist  = lambda Q: (pos.x - Q.x)**2 + (pos.y - Q.y)**2 # sqrt is monotonic

    def all_points(edge_frame):
        _, frame = edge_frame
        return sum(map(sq_dist, corners(frame)))

    acc = []
    for edge in frames:
        for frame in frames[edge]:
            acc.append((edge, frame))
    edge, frame = min(acc, key=all_points)
    frames[edge].remove(frame)
    return frame, min(corners(frame), key=sq_dist)


@coroutine
def paste_into_frame(canvas, count):
    color_selection=Color('red').range_to(Color('purple'), count+1)
    draw = ImageDraw.Draw(canvas)
    transform = lambda c: tuple(map(int, map(lambda x: x * 255, c.rgb)))

    for color in (transform(c) for c in color_selection):
        vis_im, target, position, b_box = (yield)
        frame, nearest_corner = target

        vis_im = vis_im.resize(frame.shape, Image.ANTIALIAS)
        vis_im = ImageOps.expand(vis_im, border=3, fill=color)
        canvas.paste(vis_im, frame.position)

        draw.line(nearest_corner + position, fill=color, width=2)
        t, *_, l = corners(b_box)
        draw.rectangle([t, l], outline=color)


def interface(old_im, *regions):
    orig_shape  = old_im.size
    border_size = 200

    canvas_shape = tuple(map(lambda x: x + 2*border_size, orig_shape))
    new_im = Image.new("RGB", canvas_shape)

    new_im.paste(old_im, ((canvas_shape[0]-orig_shape[0])//2,
                          (canvas_shape[1]-orig_shape[1])//2))

    frames = allocate_frames(canvas_shape, border_size)

    context = paste_into_frame(new_im, len(regions))
    for region in regions:
        pos    = Point(region.x + border_size, region.y + border_size)
        target = nearest_frame(pos, frames)
        vis_im = Image.open(region.visualization)

        bbox_loc = Point(*map(lambda x: x + border_size, region.bbox_loc))
        b_box    = Frame(position=bbox_loc, shape=region.bbox_shape)

        context.send((vis_im, target, pos, b_box))

    new_im.save('output.png', 'PNG')


def cli():
    try:
        with open(argv[2]) as fd:
            old_im, regions = Image.open(argv[1]), [Region(**i) for i in load(fd)]
    except Exception as e:
        print("Usage: {} <image-file> <regions.json>".format(argv[0]), file=stderr)
        exit(1)
    interface(old_im, *regions)


if __name__ == '__main__':
    cli()
