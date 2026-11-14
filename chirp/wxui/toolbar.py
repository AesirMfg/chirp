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

import wx

from chirp.wxui import icons
from chirp.wxui import theme

_ = wx.GetTranslation

_FILTER_TIP = _(
    'Filter memories. Search frequency, name, and comment, or enter a '
    'query such as name~"net" or freq<144,148> and press Enter.'
)


class FlatToolButton(wx.Control):
    """Borderless toolbar button with a line icon and optional label."""

    def __init__(self, parent, label, icon_name, callback, tip):
        super().__init__(parent, style=wx.BORDER_NONE)
        self._label = label or ''
        self._icon_name = icon_name
        self._callback = callback
        self._hover = False
        self._pressed = False
        self._bitmap = wx.NullBitmap
        self._disabled = wx.NullBitmap
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetLabel(self._label or tip)
        self.SetName(self._label or tip)
        self.SetToolTip(tip)
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.Bind(wx.EVT_PAINT, self._paint)
        self.Bind(wx.EVT_ENTER_WINDOW, self._enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._leave)
        self.Bind(wx.EVT_LEFT_DOWN, self._down)
        self.Bind(wx.EVT_LEFT_UP, self._up)
        self.Bind(wx.EVT_KEY_DOWN, self._key)
        self._load_bitmaps()
        size = self._best_size()
        self.SetMinSize(size)
        self.SetInitialSize(size)

    def AcceptsFocus(self):
        return self.IsEnabled()

    def AcceptsFocusFromKeyboard(self):
        return self.IsEnabled()

    def Enable(self, enable=True):
        super().Enable(enable)
        self.Refresh()

    def _icon_px(self):
        return max(16, self.FromDIP(18))

    def _load_bitmaps(self):
        colour = theme.palette().icon
        size = self._icon_px()
        self._bitmap = icons.bitmap(self._icon_name, size, colour)
        self._disabled = icons.disabled_bitmap(self._icon_name, size, colour)

    def apply_theme(self):
        self._load_bitmaps()
        self.InvalidateBestSize()
        self.SetMinSize(self._best_size())
        self.Refresh()

    def _best_size(self):
        dc = wx.MemoryDC()
        dc.SetFont(self.GetFont())
        width = self.FromDIP(16)
        height = self.FromDIP(18)
        if self._bitmap and self._bitmap.IsOk():
            width += self._bitmap.GetWidth()
            height = max(height, self._bitmap.GetHeight())
        if self._label:
            text_w, text_h = dc.GetTextExtent(self._label)
            width += text_w + self.FromDIP(8)
            height = max(height, text_h)
        return wx.Size(width, height + self.FromDIP(12))

    def DoGetBestSize(self):
        return self._best_size()

    def _enter(self, event):
        self._hover = True
        self.Refresh()

    def _leave(self, event):
        self._hover = False
        self._pressed = False
        self.Refresh()

    def _down(self, event):
        if not self.IsEnabled():
            return
        self._pressed = True
        self.CaptureMouse()
        self.Refresh()

    def _up(self, event):
        if self.HasCapture():
            self.ReleaseMouse()
        inside = self.GetClientRect().Contains(event.GetPosition())
        self._pressed = False
        self.Refresh()
        if inside and self.IsEnabled():
            self._callback()

    def _key(self, event):
        code = event.GetKeyCode()
        if code in (wx.WXK_SPACE, wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            if self.IsEnabled():
                self._callback()
            return
        event.Skip()

    def _paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        pal = theme.palette()
        width, height = self.GetClientSize()
        if not self.IsEnabled():
            background = self.GetParent().GetBackgroundColour()
        elif self._pressed:
            background = pal.pressed
        elif self._hover or self.HasFocus():
            background = pal.hover
        else:
            background = self.GetParent().GetBackgroundColour()
        dc.SetBrush(wx.Brush(background))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(0, 0, width, height)
        if self.HasFocus() and self.IsEnabled():
            dc.SetPen(wx.Pen(pal.accent, 1))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.DrawRoundedRectangle(1, 1, max(1, width - 2),
                                    max(1, height - 2), 6)
        bitmap = self._bitmap if self.IsEnabled() else self._disabled
        x = self.FromDIP(8)
        if bitmap and bitmap.IsOk():
            dc.DrawBitmap(bitmap, x, (height - bitmap.GetHeight()) // 2, True)
            x += bitmap.GetWidth() + self.FromDIP(6)
        if not self._label:
            return
        colour = pal.text if self.IsEnabled() else pal.muted
        dc.SetTextForeground(colour)
        dc.SetFont(self.GetFont())
        _tw, th = dc.GetTextExtent(self._label)
        dc.DrawText(self._label, x, (height - th) // 2)


class ChirpToolBar(wx.Panel):
    """Top toolbar: labeled radio actions, icon actions, memory filter."""

    def __init__(self, frame):
        super().__init__(frame)
        self._frame = frame
        self._silence = False
        self._buttons = {}
        self._search = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
        self._search.ShowSearchButton(True)
        self._search.ShowCancelButton(True)
        self._search.SetDescriptiveText(_('Filter memories...'))
        self._search.SetHint(_('Filter memories...'))
        self._search.SetToolTip(_FILTER_TIP)
        self._search.SetMinSize(self.FromDIP(wx.Size(220, 28)))
        self._search.Bind(wx.EVT_TEXT, self._on_text)
        self._search.Bind(wx.EVT_TEXT_ENTER, self._on_enter)
        search_event = getattr(wx, 'EVT_SEARCH', None)
        if search_event is not None:
            self._search.Bind(search_event, self._on_enter)

        row = wx.BoxSizer(wx.HORIZONTAL)
        self._add_button(row, 'download', _('Download from radio'),
                         _('Download from radio'),
                         self._frame.toolbar_download, labeled=True)
        self._add_button(row, 'upload', _('Upload to radio'),
                         _('Upload to radio'),
                         self._frame.toolbar_upload, labeled=True)
        row.AddSpacer(self.FromDIP(8))
        self._rule = wx.Panel(self, size=(1, self.FromDIP(22)))
        row.Add(self._rule, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT,
                self.FromDIP(6))
        self._add_button(row, 'open', '', _('Open'),
                         self._frame.toolbar_open, labeled=False)
        self._add_button(row, 'save', '', _('Save'),
                         self._frame.toolbar_save, labeled=False)
        self._add_button(row, 'import', '', _('Import from file'),
                         self._frame.toolbar_import, labeled=False)
        self._add_button(row, 'undo', '', _('Undo'),
                         self._frame.toolbar_undo, labeled=False)
        self._add_button(row, 'redo', '', _('Redo'),
                         self._frame.toolbar_redo, labeled=False)
        row.AddStretchSpacer()
        row.Add(self._search, 0, wx.ALIGN_CENTER | wx.RIGHT, self.FromDIP(8))

        self._border = wx.Panel(self, size=(-1, 1))
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(row, 1, wx.EXPAND | wx.ALL, self.FromDIP(4))
        outer.Add(self._border, 0, wx.EXPAND)
        self.SetSizer(outer)
        self.apply_theme()

    def _add_button(self, sizer, name, label, tip, callback, labeled):
        button = FlatToolButton(
            self, label if labeled else '', name, callback, tip)
        self._buttons[name] = button
        sizer.Add(button, 0, wx.ALIGN_CENTER | wx.RIGHT, self.FromDIP(2))

    def apply_theme(self):
        pal = theme.palette()
        self.SetBackgroundColour(pal.window)
        self._border.SetBackgroundColour(pal.line)
        self._rule.SetBackgroundColour(pal.line)
        for button in self._buttons.values():
            button.apply_theme()
        self.Refresh()

    def set_filter_enabled(self, enabled):
        self._search.Enable(bool(enabled))

    def filter_has_focus(self):
        return self._search.HasFocus()

    def set_filter_text(self, text):
        text = text or ''
        if self._search.GetValue() == text:
            return
        self._silence = True
        try:
            self._search.ChangeValue(text)
        finally:
            self._silence = False

    def sync(self, state):
        self._buttons['save'].Enable(state['save'])
        self._buttons['upload'].Enable(state['upload'])
        self._buttons['import'].Enable(state['import'])
        self._buttons['undo'].Enable(state['undo'])
        self._buttons['redo'].Enable(state['redo'])
        self._buttons['undo'].SetToolTip(state['undo_help'])
        self._buttons['redo'].SetToolTip(state['redo_help'])

    def _on_text(self, event):
        if not self._silence:
            self._frame.on_memory_filter(self._search.GetValue(), False)
        event.Skip()

    def _on_enter(self, event):
        self._frame.on_memory_filter(self._search.GetValue(), True)
        event.Skip()
