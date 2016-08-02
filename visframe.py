#!/usr/bin/env python

from PIL import Image
from sys import argv, stderr
from itertools import islice
from collections import namedtuple, defaultdict

def window(iterable, size):
    it = iter(iterable)
    
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result


Point = namedtuple('Point', ['x', 'y'])
Frame = namedtuple('Frame', ['position', 'shape'])


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
    return (top_left, top_right, bot_left, bot_right)
    

def nearest_frame(pos, frames):
    def all_points(edge_frame):
        _, frame = edge_frame
        sq_dist  = lambda Q: (pos.x - Q.x)**2 + (pos.y - Q.y)**2
        return sum(map(sq_dist, corners(frame)))

    acc = []
    for edge in frames:
        for frame in frames[edge]:
            acc.append((edge, frame))
    edge, frame = min(acc, key=all_points)
    frames[edge].remove(frame)
    return frame


def interface(old_im, vis_im, x, y):
    orig_shape = old_im.size

    border_size = 200
    position = Point(x + border_size, y + border_size)

    canvas_shape = tuple(map(lambda x: x + 2*border_size, orig_shape))
    new_im = Image.new("RGB", canvas_shape) ## luckily, this is already black!

    new_im.paste(old_im, ((canvas_shape[0]-orig_shape[0])//2,
                          (canvas_shape[1]-orig_shape[1])//2))

    frames = allocate_frames(canvas_shape, border_size)

    for _ in range(15):
        target = nearest_frame(position, frames)
        new_im = paste_into_frame(new_im, target, vis_im)

    new_im.save('output.png', 'PNG')


def paste_into_frame(canvas, frame, vis_im):
    vis_im = vis_im.resize(frame.shape, Image.ANTIALIAS)
    canvas.paste(vis_im, frame.position)
    return canvas
    

def cli():
    try:
        old_im, vis_im, x, y = Image.open(argv[1]), Image.open(argv[2]), int(argv[3]), int(argv[4])
    except:
        print("Usage {} <image-file> <visualization> <x> <y>".format(argv[0]), file=stderr)
        exit(1)
    interface(old_im, vis_im, x, y)


if __name__ == '__main__':
    cli()
