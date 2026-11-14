# Copyright 2026 CHIRP Contributors <developers@lists.chirpmyradio.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

import wx

LOG = logging.getLogger(__name__)

# 24x24 line icons. wx.BitmapBundle.FromSVG (NanoSVG) renders these at
# the toolbar's DPI so they stay sharp on HiDPI displays.
_BODIES = {
    'download': (
        '<path d="M12 4v11"/>'
        '<path d="m7 11 5 5 5-5"/>'
        '<path d="M5 20h14"/>'
    ),
    'upload': (
        '<path d="M12 20V9"/>'
        '<path d="m7 13 5-5 5 5"/>'
        '<path d="M5 4h14"/>'
    ),
    'open': (
        '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8'
        'a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>'
    ),
    'save': (
        '<path d="M5 3h11l4 4v14H5Z"/>'
        '<path d="M8 3v5h8"/>'
        '<path d="M8 21v-7h8v7"/>'
    ),
    'import': (
        '<path d="M4 12h11"/>'
        '<path d="m11 8 4 4-4 4"/>'
        '<path d="M20 5v14"/>'
    ),
    'undo': (
        '<path d="M9 14 4 9l5-5"/>'
        '<path d="M4 9h11a5 5 0 0 1 0 10H12"/>'
    ),
    'redo': (
        '<path d="m15 14 5-5-5-5"/>'
        '<path d="M20 9H9a5 5 0 0 0 0 10h3"/>'
    ),
    'radio': (
        '<rect x="8" y="3" width="8" height="18" rx="2"/>'
        '<path d="M10 7h4"/>'
        '<circle cx="12" cy="16" r="1.4"/>'
    ),
}

_CACHE = {}


def _colour_hex(colour):
    if isinstance(colour, str):
        return colour
    return '#%02X%02X%02X' % (colour.Red(), colour.Green(), colour.Blue())


def _wx_colour(colour):
    if isinstance(colour, wx.Colour):
        return colour
    text = colour.lstrip('#')
    red = int(text[0:2], 16)
    green = int(text[2:4], 16)
    blue = int(text[4:6], 16)
    return wx.Colour(red, green, blue)


def _svg(name, colour):
    template = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
        'viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="1.75" '
        'stroke-linecap="round" stroke-linejoin="round">%s</svg>'
    )
    return (template % (colour, _BODIES[name])).encode('utf-8')


def _fallback(size, colour):
    bitmap = wx.Bitmap(size, size, 32)
    dc = wx.MemoryDC(bitmap)
    dc.SetBackground(wx.Brush(wx.Colour(0, 0, 0, wx.ALPHA_TRANSPARENT)))
    dc.Clear()
    dc.SetPen(wx.Pen(_wx_colour(colour), 2))
    inset = max(3, size // 6)
    dc.DrawLine(inset, size // 2, size - inset, size // 2)
    dc.SelectObject(wx.NullBitmap)
    return bitmap


def bitmap(name, size, colour):
    """Return a square line-icon bitmap for the given CSS-style colour."""
    hex_colour = _colour_hex(colour)
    key = (name, int(size), hex_colour)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached
    rendered = None
    try:
        bundle = wx.BitmapBundle.FromSVG(
            _svg(name, hex_colour), wx.Size(size, size))
        rendered = bundle.GetBitmap(wx.Size(size, size))
    except Exception:
        LOG.exception('Failed to render icon %s', name)
    if rendered is None or not rendered.IsOk() or rendered.GetWidth() <= 0:
        rendered = _fallback(size, hex_colour)
    _CACHE[key] = rendered
    return rendered


def disabled_bitmap(name, size, colour):
    key = ('disabled', name, int(size), _colour_hex(colour))
    cached = _CACHE.get(key)
    if cached is not None:
        return cached
    image = bitmap(name, size, colour).ConvertToImage()
    rendered = wx.Bitmap(image.ConvertToDisabled(170))
    _CACHE[key] = rendered
    return rendered
