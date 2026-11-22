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

# Pill fills and text colours, keyed by mode name or power group.
# Light pairs are (background, foreground). Dark uses the same keys.
_PILLS_LIGHT = {
    'FM': ((219, 234, 254), (29, 78, 216)),
    'NFM': ((209, 250, 229), (4, 120, 87)),
    'WFM': ((224, 231, 255), (67, 56, 202)),
    'AM': ((255, 237, 213), (194, 65, 12)),
    'DV': ((237, 233, 254), (109, 40, 217)),
    'USB': ((207, 250, 254), (14, 116, 144)),
    'LSB': ((207, 250, 254), (14, 116, 144)),
    'CW': ((254, 243, 199), (146, 64, 14)),
    'CWR': ((254, 243, 199), (146, 64, 14)),
    'DIG': ((252, 231, 243), (157, 23, 77)),
    'RTTY': ((252, 231, 243), (157, 23, 77)),
    'PKT': ((252, 231, 243), (157, 23, 77)),
    'high': ((220, 252, 231), (21, 128, 61)),
    'mid': ((255, 237, 213), (194, 65, 12)),
    'low': ((241, 245, 249), (71, 85, 105)),
    'neutral': ((241, 245, 249), (51, 65, 85)),
}

_PILLS_DARK = {
    'FM': ((30, 58, 95), (147, 197, 253)),
    'NFM': ((6, 78, 59), (110, 231, 183)),
    'WFM': ((49, 46, 129), (165, 180, 252)),
    'AM': ((124, 45, 18), (254, 215, 170)),
    'DV': ((76, 29, 149), (196, 181, 253)),
    'USB': ((22, 78, 99), (103, 232, 249)),
    'LSB': ((22, 78, 99), (103, 232, 249)),
    'CW': ((120, 53, 15), (253, 230, 138)),
    'CWR': ((120, 53, 15), (253, 230, 138)),
    'DIG': ((131, 24, 67), (251, 207, 232)),
    'RTTY': ((131, 24, 67), (251, 207, 232)),
    'PKT': ((131, 24, 67), (251, 207, 232)),
    'high': ((6, 78, 59), (134, 239, 172)),
    'mid': ((124, 45, 18), (254, 215, 170)),
    'low': ((51, 65, 85), (203, 213, 225)),
    'neutral': ((51, 65, 85), (226, 232, 240)),
}

_DV_NAMES = ('DV', 'D-STAR', 'DSTAR', 'DSTAR', 'FUSION', 'DMR', 'P25')


def luminance(colour):
    return (0.299 * colour.Red() + 0.587 * colour.Green() +
            0.114 * colour.Blue())


def is_dark():
    """True when the running system theme is dark."""
    window = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
    luma = luminance(window)
    if luma < 110:
        return True
    if luma > 180:
        return False
    appearance = getattr(wx.SystemSettings, 'GetAppearance', None)
    if appearance is None:
        return luma < 140
    try:
        return bool(appearance().IsDark())
    except Exception:
        LOG.debug('System appearance is unavailable', exc_info=True)
        return luma < 140


def blend(left, right, amount):
    """Mix two colours. amount=0 returns left, amount=1 returns right."""
    def channel(a, b):
        return int(a + (b - a) * amount)

    return wx.Colour(channel(left.Red(), right.Red()),
                     channel(left.Green(), right.Green()),
                     channel(left.Blue(), right.Blue()))


def _hex(colour):
    return '#%02X%02X%02X' % (colour.Red(), colour.Green(), colour.Blue())


class Palette:
    """Colours for the chrome we paint ourselves.

    Window, text, and face colours come from the system theme so a
    GTK/Windows/macOS dark theme changes the whole window. Selection
    and accent colours are chosen to match that brightness.
    """

    def __init__(self):
        self.dark = is_dark()
        self.window = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        self.text = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        self.face = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE)
        self.muted = wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        stripe = 0.07 if self.dark else 0.045
        self.line = blend(self.window, self.text, 0.14 if self.dark else 0.10)
        self.zebra = blend(self.window, self.text, stripe)
        self.header = blend(self.window, self.face, 0.7)
        self.hover = blend(self.window, self.text, 0.06)
        self.pressed = blend(self.window, self.text, 0.12)
        self.sidebar = blend(self.window, self.face, 0.45)
        self.immutable = blend(self.window, self.text, 0.08)
        self.icon = _hex(self.text)
        if self.dark:
            self.selection = wx.Colour(38, 70, 120)
            self.selection_text = wx.Colour(232, 240, 254)
            self.accent = wx.Colour(138, 180, 248)
            self.connected = wx.Colour(52, 168, 83)
        else:
            self.selection = wx.Colour(219, 234, 254)
            self.selection_text = wx.Colour(30, 41, 59)
            self.accent = wx.Colour(37, 99, 235)
            self.connected = wx.Colour(22, 163, 74)


def palette():
    return Palette()


def _power_key(text):
    if 'HIGH' in text or text in ('H', 'HI'):
        return 'high'
    if 'LOW' in text or text in ('L', 'LO'):
        return 'low'
    if 'MID' in text or 'MED' in text or text == 'M':
        return 'mid'
    return 'neutral'


def _pill_key(kind, value):
    text = (value or '').strip().upper()
    if kind == 'power':
        return _power_key(text)
    if text in _DV_NAMES:
        return 'DV'
    if text in _PILLS_LIGHT:
        return text
    return 'neutral'


def pill_colours(kind, value):
    """Return (background, foreground) for a mode or power badge."""
    table = _PILLS_DARK if is_dark() else _PILLS_LIGHT
    background, foreground = table[_pill_key(kind, value)]
    return wx.Colour(*background), wx.Colour(*foreground)


def _enable_windows_dark_mode(app):
    enable = getattr(app, 'MSWEnableDarkMode', None)
    if enable is None:
        return
    try:
        enable()
    except TypeError:
        try:
            enable(True)
        except Exception:
            LOG.debug('MSWEnableDarkMode failed', exc_info=True)
    except Exception:
        LOG.debug('MSWEnableDarkMode failed', exc_info=True)


def install(app):
    """Ask wx to follow the system light/dark appearance."""
    appearance = getattr(app, 'Appearance', None)
    setter = getattr(app, 'SetAppearance', None)
    if appearance is not None and setter is not None:
        try:
            setter(appearance.System)
        except Exception:
            LOG.debug('SetAppearance(System) failed', exc_info=True)
    _enable_windows_dark_mode(app)
