from PIL import Image
import os

#Many thanks to Yepoleb for their TileCodecs scripts!

class TileCodec(object):
    """
    Abstract class for 8x8 ("atomic") tile codecs.
    To add a new tile format, simply extend this class and implement
    decode() and encode().
    """

    def __init__(self, bpp, stride=0):
        """
        Base class constructor. Every subclass must call this with argument bpp.

        Arguments:
        bpp - Bits per pixel
        stride - 0 for MODE_1D, -1 + (# of tile columns in your final image)
                 for MODE_2D. I have no idea why this exists
        """
        self.bits_per_pixel = bpp
        self.bytes_per_row = bpp # 8 pixel per row / 8 bits per byte
        self.stride = stride * self.bytes_per_row
        self.tile_size = self.bytes_per_row * 8 # 8 rows per tile
        self.color_count = 1 << bpp


    def decode(self, bits, ofs=0):
        """
        Decodes a tile. Has to be implemented by subclasses.

        Arguments:
        bits - A bytes-like object of encoded tile data
        ofs - Start offset of tile in bits
        """
        raise NotImplementedError


    def encode(self, pixels, bits=None, ofs=0):
        """
        Encodes a tile. Has to be implemented by subclasses.

        Arguments:
        pixels - A list of decoded tile data
        bits - A bytearray object to encode the data into
        ofs - Start offset of tile in bits
        """
        raise NotImplementedError

    def checkBitsLength(self, bits, ofs):
        """
        Checks if the amount of remaining pixels is bigger than the tilesize.
        """
        if len(bits) - ofs < self.tile_size:
            raise IndexError("Bits input too short. Required {}b, got {}b"\
                .format(ofs+self.tile_size, len(bits)))

    def getBitsPerPixel(self):
        """
        Gets the # of bits per pixel for the tile format.
        """
        return self.bits_per_pixel


    def getBytesPerRow(self):
        """
        Gets the # of bytes per row (8 pixels) for the tile format.
        """
        return self.bytes_per_row


    def getColorCount(self):
        """
        Gets the # of colors for the tile format
        """
        return self.color_count


    def getTileSize(self):
        """
        Gets the size in bytes of one tile encoded in this format.
        """
        return self.tile_size


class LinearCodec(TileCodec):
    """
    Linear palette-indexed 8x8 tile codec.
    """

    IN_ORDER = 1
    REVERSE_ORDER = 2

    def __init__(self, bpp, ordering=None, stride=0):
        """
        Constructor for LinearCodec

        Arguments:
        bpp - Bits per pixel
        ordering - See explanation above
        stride - 0 for MODE_1D, -1 + (# of tile columns in your final image)
                 for MODE_2D. I have no idea why this exists
        """
        TileCodec.__init__(self, bpp, stride)
        self.pixels_per_byte = 8 // self.bits_per_pixel
        self.pixel_mask = (1 << self.bits_per_pixel) - 1 # e.g. 0b1111 for 4bpp

        if ordering is None:
            ordering = self.IN_ORDER
        self.ordering = ordering

        if self.ordering == self.IN_ORDER:
            self.start_pixel = self.pixels_per_byte-1
            self.boundary = -1
            self.step = -1

        else:  # REVERSE_ORDER
            self.start_pixel = 0
            self.boundary = self.pixels_per_byte
            self.step = 1

    def decode(self, bits, ofs=0, leng=8):
        """
        Decodes a tile.

        Arguments:
        bits - A bytes-like object of encoded tile data
        ofs - Start offset of tile in bits
        """
        self.checkBitsLength(bits, ofs)

        pixels = []
        for i_row in range(leng):
            # do one row
            for i_byte in range(self.bytes_per_row):
                # do one byte
                pos = ofs + i_row*(self.bytes_per_row + self.stride) + i_byte
                byte = bits[pos]
                for i_pixel in range(self.start_pixel, self.boundary, self.step):
                    # decode one pixel
                    pixel = (byte >> self.bits_per_pixel*i_pixel) & self.pixel_mask
                    pixels.append(pixel)

        return pixels


    def encode(self, pixels, bits=None, ofs=0):
        """
        Encodes a tile.

        Arguments:
        pixels - A list of decoded tile data
        bits - A bytearray object to encode the data into
        ofs - Start offset of tile in bits
        """
        if bits is None:
            bits = b"\x00" * (self.tile_size)
        bits = bytearray(bits)

        self.checkBitsLength(bits, ofs)

        for i_row in range(8):
            # do one row
            for i_byte in range(self.bytes_per_row):
                # do one byte
                pos = ofs + i_row*(self.bytes_per_row + self.stride) + i_byte
                byte = 0
                for i_pixel in range(self.start_pixel, self.boundary, self.step):
                    # encode one pixel
                    pixel_pos = i_row*8 + i_byte*self.pixels_per_byte + i_pixel
                    byte |= (pixels[pixel_pos] & self.pixel_mask) << \
                            (i_pixel*self.bits_per_pixel)
                bits[pos] = byte

        return bits



for i in [i.name for i in os.scandir("btlbadge")]:
    a = LinearCodec(4, 2)
    with open(f"badge/{i}", "rb") as f:
        bytedata = f.read()
    pin = []
    for j in range(132, 644, 16):
        b = a.decode(bytedata, j, leng=4)
        pin += [j * 8 for j in b]

    img = Image.new("L", (32, 32))
    img.putdata(pin)
    img.save(f"res/{i}.png")
