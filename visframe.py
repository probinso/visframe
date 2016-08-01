#!/usr/bin/env python

from PIL import Image
from sys import argv, stderr


def interface(old_im, vis_im):
    old_size = old_im.size

    bordersize = 200
    new_size = tuple(map(lambda x: x + 2*bordersize, old_size))
    new_im = Image.new("RGB", new_size) ## luckily, this is already black!
    new_im.paste(old_im, ((new_size[0]-old_size[0])//2,
                          (new_size[1]-old_size[1])//2))

    new_im.show()


def cli():
    try:
        old_im, vis_im = Image.open(argv[1]), Image.open(argv[2])
    except:
        print("Usage {} <image-file> <visualization>".format(argv[0]), file=stderr)
        exit(1)
    interface(old_im)


if __name__ == '__main__':
    cli()
