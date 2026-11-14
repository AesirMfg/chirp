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

import os

import wx

from chirp.wxui import icons
from chirp.wxui import theme

_ = wx.GetTranslation


def port_label(radio):
    """Human description of how a radio is connected."""
    pipe = getattr(radio, 'pipe', None)
    if pipe is None:
        return _('not connected')
    for attr in ('port', 'name', 'device'):
        value = getattr(pipe, attr, None)
        if not value:
            continue
        text = str(value)
        if text and text != 'None':
            return text
    return _('connected')


def radio_connected(radio):
    return getattr(radio, 'pipe', None) is not None


class _RadioRow(wx.Control):
    def __init__(self, parent, item, on_activate):
        super().__init__(parent, style=wx.BORDER_NONE)
        self._item = item
        self._on_activate = on_activate
        self._icon = wx.NullBitmap
        self._icon_key = None
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetMinSize(self.FromDIP(wx.Size(-1, 56)))
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.Bind(wx.EVT_PAINT, self._paint)
        self.Bind(wx.EVT_LEFT_UP, self._activate)
        self.Bind(wx.EVT_KEY_DOWN, self._key)
        self.update(item)

    def AcceptsFocus(self):
        return True

    def AcceptsFocusFromKeyboard(self):
        return True

    def update(self, item):
        self._item = item
        self.SetLabel(item['title'])
        self.SetName(item['title'])
        tip = item['subtitle'] or item['title']
        self.SetToolTip(tip)
        self.Refresh()

    def _activate(self, event):
        self._on_activate(self._item['index'])

    def _key(self, event):
        code = event.GetKeyCode()
        if code in (wx.WXK_SPACE, wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            self._on_activate(self._item['index'])
            return
        event.Skip()

    def _bitmap(self, colour):
        key = (colour, self.FromDIP(18))
        if key != self._icon_key:
            self._icon = icons.bitmap('radio', self.FromDIP(18), colour)
            self._icon_key = key
        return self._icon

    def _text_colours(self, pal, selected):
        if not selected:
            return pal.text, pal.muted
        subtitle = theme.blend(pal.selection, pal.selection_text, 0.72)
        return pal.selection_text, subtitle

    def _paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        pal = theme.palette()
        width, height = self.GetClientSize()
        selected = bool(self._item.get('selected'))
        dc.SetBrush(wx.Brush(pal.sidebar))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(0, 0, width, height)
        if selected:
            dc.SetBrush(wx.Brush(pal.selection))
            dc.DrawRoundedRectangle(4, 3, max(1, width - 8),
                                    max(1, height - 6), 8)
        title_colour, sub_colour = self._text_colours(pal, selected)
        bitmap = self._bitmap(pal.icon)
        icon_x = self.FromDIP(14)
        if bitmap and bitmap.IsOk():
            dc.DrawBitmap(bitmap, icon_x,
                          (height - bitmap.GetHeight()) // 2, True)
            if self._item.get('connected'):
                dc.SetBrush(wx.Brush(pal.connected))
                dc.SetPen(wx.Pen(pal.sidebar, 1))
                dot = self.FromDIP(7)
                dc.DrawCircle(icon_x + bitmap.GetWidth() - 1,
                              (height + bitmap.GetHeight()) // 2 - 1, dot // 2)
            text_x = icon_x + bitmap.GetWidth() + self.FromDIP(10)
        else:
            text_x = icon_x
        max_w = max(20, width - text_x - self.FromDIP(10))
        title_font = wx.Font(self.GetFont())
        if selected:
            title_font.SetWeight(wx.FONTWEIGHT_SEMIBOLD)
        dc.SetFont(title_font)
        title = wx.Control.Ellipsize(
            self._item['title'], dc, wx.ELLIPSIZE_END, max_w)
        _tw, th = dc.GetTextExtent(title)
        subtitle = self._item.get('subtitle') or ''
        if subtitle:
            y = max(6, (height - th - self.FromDIP(16)) // 2)
        else:
            y = (height - th) // 2
        dc.SetTextForeground(title_colour)
        dc.DrawText(title, text_x, y)
        if not subtitle:
            return
        sub_font = wx.Font(self.GetFont())
        sub_font.SetPointSize(max(8, sub_font.GetPointSize() - 1))
        dc.SetFont(sub_font)
        dc.SetTextForeground(sub_colour)
        shown = self._subtitle(dc, max_w)
        dc.DrawText(shown, text_x, y + th + 2)

    def _subtitle(self, dc, max_width):
        filename = self._item.get('filename') or ''
        port = self._item.get('port') or ''
        if filename and port:
            sep = ' · '
            port_w = dc.GetTextExtent(sep + port)[0]
            file_w = max(24, max_width - port_w)
            shown_file = wx.Control.Ellipsize(
                filename, dc, wx.ELLIPSIZE_END, file_w)
            return shown_file + sep + port
        text = self._item.get('subtitle') or ''
        return wx.Control.Ellipsize(text, dc, wx.ELLIPSIZE_END, max_width)


class ChirpRadioSidebar(wx.Panel):
    """List of open radio images. The file tabs remain for close and drag."""

    def __init__(self, frame):
        super().__init__(frame)
        self._frame = frame
        self._key = None
        self._rows = []
        self._caption = wx.StaticText(self, label=_('Open radios'))
        caption_font = self._caption.GetFont()
        caption_font.SetPointSize(max(8, caption_font.GetPointSize() - 1))
        caption_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self._caption.SetFont(caption_font)

        self._scroll = wx.ScrolledWindow(self, style=wx.VSCROLL)
        self._scroll.SetScrollRate(0, self.FromDIP(16))
        self._items = wx.BoxSizer(wx.VERTICAL)
        self._scroll.SetSizer(self._items)

        inner = wx.BoxSizer(wx.VERTICAL)
        inner.Add(self._caption, 0, wx.LEFT | wx.RIGHT | wx.TOP,
                  self.FromDIP(12))
        inner.Add(self._scroll, 1, wx.EXPAND | wx.ALL, self.FromDIP(6))
        self._border = wx.Panel(self, size=(1, -1))
        outer = wx.BoxSizer(wx.HORIZONTAL)
        outer.Add(inner, 1, wx.EXPAND)
        outer.Add(self._border, 0, wx.EXPAND)
        self.SetSizer(outer)
        self.SetMinSize(self.FromDIP(wx.Size(232, -1)))
        self.apply_theme()

    def apply_theme(self):
        pal = theme.palette()
        self.SetBackgroundColour(pal.sidebar)
        self._scroll.SetBackgroundColour(pal.sidebar)
        self._caption.SetForegroundColour(pal.muted)
        self._border.SetBackgroundColour(pal.line)
        for row in self._rows:
            row.Refresh()
        self.Refresh()

    def refresh(self):
        pages = self._describe()
        key = tuple(item['id'] for item in pages)
        if key != self._key:
            self._rebuild(pages)
            self._key = key
        else:
            for item, row in zip(pages, self._rows):
                row.update(item)

    def _describe(self):
        book = self._frame._editors
        current = book.GetSelection()
        pages = []
        for index in range(book.GetPageCount()):
            pages.append(self._describe_page(
                index, book.GetPage(index), index == current))
        return pages

    def _describe_page(self, index, page, selected):
        radio = getattr(page, 'radio', None)
        if radio is None:
            return {
                'id': page.GetId(),
                'index': index,
                'title': _('Welcome'),
                'subtitle': '',
                'connected': False,
                'selected': selected,
            }
        vendor = getattr(radio, 'VENDOR', '') or ''
        model = getattr(radio, 'MODEL', '') or ''
        title = ('%s %s' % (vendor, model)).strip() or _('Radio')
        if getattr(page, 'modified', False):
            title += '*'
        filename = os.path.basename(getattr(page, 'filename', '') or '')
        port = port_label(radio)
        if filename:
            subtitle = '%s · %s' % (filename, port)
        else:
            subtitle = port
        return {
            'id': page.GetId(),
            'index': index,
            'title': title,
            'subtitle': subtitle,
            'filename': filename,
            'port': port,
            'connected': radio_connected(radio),
            'selected': selected,
        }

    def _rebuild(self, pages):
        self._items.Clear(delete_windows=True)
        self._rows = []
        for item in pages:
            row = _RadioRow(self._scroll, item, self._frame.select_editor_page)
            self._rows.append(row)
            self._items.Add(row, 0, wx.EXPAND | wx.BOTTOM, 2)
        self._scroll.Layout()
        self._scroll.FitInside()

    def select_page(self, index):
        self._frame.select_editor_page(index)
