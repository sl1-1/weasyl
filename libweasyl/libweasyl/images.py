# encoding: utf-8

"""
Image manipulation with Pillow.
"""
import copy
from io import BytesIO

from PIL import Image, ImageSequence

COVER_SIZE = 1024, 3000
"The maximum size of a cover image, in pixels."

THUMB_HEIGHT = 250
"The maximum height of a thumbnail, in pixels."


def process_gif(image: Image.Image, action, args):
    image_frames = ImageSequence.Iterator(image)

    # Wrap on-the-fly thumbnail generator
    def thumbnails(frames):
        for frame in frames:
            thumbnail = frame.copy()
            func = getattr(thumbnail, action)
            thumbnail = func(**args)
            yield thumbnail

    thumbnail_frames = thumbnails(image_frames)

    # Save output
    om = next(thumbnail_frames)  # Handle first frame separately
    om.info = image.info  # Copy sequence info
    with BytesIO() as out:
        om.save(out, format=image.format, save_all=True, append_images=list(thumbnail_frames))
        image_data = out.getvalue()
    return image_data, om.size


class WeasylImage:
    _file_format = None
    image_data = bytes()
    webp = None
    _size = (0, 0)

    def __init__(self, fp=None, string=None):
        if string:
            self.image_data = string
        elif fp:
            with open(fp, 'rb') as in_file:
                self.image_data = BytesIO(in_file.read()).getvalue()
        else:
            raise IOError
        with BytesIO(self.image_data) as image_bytes:
            image = Image.open(image_bytes)
            self._file_format = image.format
            self._size = image.size
            self.is_animated = getattr(image, 'is_animated', False)

    @property
    def attributes(self):
        return {'width': self._size[0], 'height': self._size[1]}

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        raise AttributeError('Use resize to change size')

    @property
    def file_format(self):
        if self._file_format == "JPEG":
            return "jpg"
        else:
            return self._file_format.lower()

    @property
    def image_extension(self):
        return ".{}".format(self.file_format)


    def to_buffer(self):
        return self.image_data

    def save(self, fp):
        with open(fp, 'wb') as out:
            out.write(self.image_data)

    def resize(self, size: (int, int)):
        """
        Resize the image if necessary. Will not resize images that fit entirely
        within target dimensions.

        Parameters:
            size: Tuple (width, height)
        """
        with BytesIO(self.image_data) as image_bytes:
            image = Image.open(image_bytes)
            if image.size[0] > size[0] or image.size[1] > size[1]:
                if not getattr(image, 'is_animated', False):
                    image.thumbnail(size)
                    self._size = image.size
                    with BytesIO() as out:
                        image.save(out, format=self._file_format)
                        self.image_data = out.getvalue()

                else:
                    self.image_data, self._size = process_gif(image, 'resize', {'size': size})

    def crop(self, bounds: (int, int, int, int)):
        """
        Crops the image using the bounds provided
        :param bounds: tuple of ( left, upper, right, lower)
        :return: None
        """
        with BytesIO(self.image_data) as image_bytes:
            image = Image.open(image_bytes)
            # resize only if we need to; return None if we don't
            if not getattr(image, 'is_animated', False):
                image = image.crop(bounds)
                self._size = image.size
                with BytesIO() as out:
                    image.save(out, format=self._file_format)
                    self.image_data = out.getvalue()

            else:
                self.image_data, self._size = process_gif(image, 'crop', {'box': bounds})

    def shrinkcrop(self, size: (int, int), bounds: (int, int, int, int) = None):
        """

        :param size: tuple of (width, height)
        :param bounds: tuple of (left, upper, right, lower)
        :return: None
        """
        if bounds:
            if bounds[0:2] != (0, 0) or bounds[2:4] != self._size:
                self.crop(bounds)
            if self._size != size:
                self.resize(size)
            return
        elif self._size == size:
            return
        shrunk_size = _fit_inside((0, 0, size[0], size[1]), self._size)
        if self._size != shrunk_size:
            self.resize((shrunk_size[2:4]))
        x1 = (self._size[0] - size[0]) // 2
        y1 = (self._size[1] - size[1]) // 2
        bounds = (x1, y1, x1 + size[0], y1 + size[1])
        self.crop(bounds)

    def get_thumbnail(self, bounds: (int, int, int, int) = None):
        save_kwargs = {}
        with BytesIO(self.image_data) as image_bytes:
            image = Image.open(image_bytes)
            if image.mode in ('1', 'L', 'LA', 'I', 'P'):
                image = image.convert(mode='RGBA' if image.mode == 'LA' or 'transparency' in image.info else 'RGB')

            if bounds is None:
                source_rect, result_size = get_thumbnail_spec(image.size, THUMB_HEIGHT)
            else:
                source_rect, result_size = get_thumbnail_spec_cropped(
                    _fit_inside(bounds, image.size),
                    THUMB_HEIGHT)
            if source_rect == (0, 0, image.width, image.height):
                image.draft(None, result_size)
                image = image.resize(result_size, resample=Image.LANCZOS)
            else:
                # TODO: draft and adjust rectangle?
                image = image.resize(result_size, resample=Image.LANCZOS, box=source_rect)

            if self._file_format == 'JPEG':
                with BytesIO() as f:
                    image.save(f, format='JPEG', quality=95, optimize=True, progressive=True, subsampling='4:2:2')
                    compatible = (f.getvalue(), 'JPG')

                lossless = False
            elif self._file_format in ('PNG', 'GIF'):
                with BytesIO() as f:
                    image.save(f, format='PNG', optimize=True, **save_kwargs)
                    compatible = (f.getvalue(), 'PNG')

                lossless = True
            else:
                raise Exception("Unexpected image format: %r" % (self._file_format,))

            with BytesIO() as f:
                image.save(f, format='WebP', lossless=lossless, quality=100 if lossless else 90, method=6,
                           **save_kwargs)
                webp = (f.getvalue(), 'WEBP')

            if not len(webp[0]) >= len(compatible[0]):
                self.webp = webp[0]

            self._file_format = compatible[1]
            self.image_data = compatible[0]
            self._size = image.size

    def copy(self):
        """
        Creates a deep copy of the image class
        :return: WeasylImage()
        """
        return copy.deepcopy(self)


def get_thumbnail_spec(size, height):
    """
    Get the source rectangle (x, y, x + w, y + h) and result size (w, h) for
    the thumbnail of the specified height of an image with the specified size.
    """
    size_width, size_height = size

    max_source_width = 2 * max(size_height, height)
    max_source_height = max(2 * size_width, height)

    source_width = min(size_width, max_source_width)
    source_height = min(size_height, max_source_height)
    source_left = (size_width - source_width) // 2
    source_top = 0

    result_height = min(size_height, height)
    result_width = (source_width * result_height + source_height // 2) // source_height

    return (
        (source_left, source_top, source_left + source_width, source_top + source_height),
        (result_width, result_height),
    )


def get_thumbnail_spec_cropped(rect, height):
    """
    Get the source rectangle and result size for the thumbnail of the specified
    height of a specified rectangular section of an image.
    """
    left, top, right, bottom = rect
    inner_rect, result_size = get_thumbnail_spec((right - left, bottom - top), height)
    inner_left, inner_top, inner_right, inner_bottom = inner_rect

    return (inner_left + left, inner_top + top, inner_right + left, inner_bottom + top), result_size


def _fit_inside(rect, size):
    left, top, right, bottom = rect
    width, height = size

    return (
        max(0, left),
        max(0, top),
        min(width, right),
        min(height, bottom),
    )


def check_crop(dim, x1, y1, x2, y2):
    """
    Return True if the specified crop coordinates are valid, else False.
    """
    return (
        x1 >= 0 and y1 >= 0 and x2 >= 0 and y2 >= 0 and x1 <= dim[0] and
        y1 <= dim[1] and x2 <= dim[0] and y2 <= dim[1] and x2 > x1 and y2 > y1)

