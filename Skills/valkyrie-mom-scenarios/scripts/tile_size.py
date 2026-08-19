#!/usr/bin/env python3
"""Computes the size in squares of a Mansions of Madness tile from its .dds
image as imported by Valkyrie.

Formula (Valkyrie engine, MoM, non-Android), confirmed in
unity/Assets/Scripts/GameType.cs (class MoMGameType.TilePixelPerSquare):
    1024 px = 3.5 squares  =>  1 square = 1024/3.5 px

Usage:
    python3 tile_size.py Tile_Bedroom_1_MAD20.dds [another.dds ...]
"""
import struct
import sys

PPS = 1024 / 3.5  # pixels per square


def dds_dimensions(path):
    with open(path, "rb") as f:
        magic = f.read(4)
        if magic != b"DDS ":
            raise ValueError(f"{path}: not a valid DDS file (magic={magic!r})")
        header = f.read(124)
        height = struct.unpack_from("<I", header, 8)[0]
        width = struct.unpack_from("<I", header, 12)[0]
        return width, height


def tile_squares(path):
    w, h = dds_dimensions(path)
    return round(w / PPS, 4), round(h / PPS, 4), w, h


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for path in sys.argv[1:]:
        try:
            w_sq, h_sq, w_px, h_px = tile_squares(path)
        except Exception as e:
            print(f"ERROR {path}: {e}")
            continue
        print(f"{path}")
        print(f"  {w_px}x{h_px} px  ->  {w_sq} x {h_sq} squares (width x height)")


if __name__ == "__main__":
    main()
