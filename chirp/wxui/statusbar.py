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

from chirp.wxui import theme

_ = wx.GetTranslation


class ChirpStatusBar(wx.Panel):
    """Model, port, memory count, and the transient editor message."""

    def __init__(self, parent):
        super().__init__(parent)
        self._model_text = ''
        self._port_text = ''
        self._count_text = ''
        self._connected = False
        self._message = ''

        self._dot = wx.StaticText(self, label='●')
        self._model = wx.StaticText(self)
        self._port = wx.StaticText(self)
        self._count = wx.StaticText(self)
        self._msg = wx.StaticText(self, label=_('Ready'))
        self._rule = wx.Panel(self, size=(-1, 1))

        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(self._dot, 0, wx.ALIGN_CENTER | wx.LEFT, 10)
        row.Add(self._model, 0, wx.ALIGN_CENTER | wx.LEFT, 6)
        row.Add(self._port, 0, wx.ALIGN_CENTER | wx.LEFT, 16)
        row.Add(self._count, 0, wx.ALIGN_CENTER | wx.LEFT, 16)
        row.AddStretchSpacer()
        row.Add(self._msg, 0, wx.ALIGN_CENTER | wx.RIGHT, 12)

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(self._rule, 0, wx.EXPAND)
        outer.Add(row, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 4)
        self.SetSizer(outer)
        self.SetMinSize(self.FromDIP(wx.Size(-1, 28)))
        self.apply_theme()

    def apply_theme(self):
        self._render()

    def set_radio(self, model, port, count, connected):
        self._model_text = model or ''
        self._port_text = port or ''
        self._count_text = count or ''
        self._connected = bool(connected and model)
        self._render()

    def set_message(self, text):
        self._message = text or ''
        self._render()

    def SetStatusText(self, text, i=0):
        """Compatibility with the old two-field status bar.

        Field 0 is the transient message. Field 1 used to be the model.
        """
        if i == 0:
            self.set_message(text)
        elif i == 1 and text:
            self._model_text = text
            self._render()

    def _render(self):
        pal = theme.palette()
        self.SetBackgroundColour(pal.face)
        self._rule.SetBackgroundColour(pal.line)
        self._model.SetLabel(self._model_text)
        self._port.SetLabel(self._port_text)
        self._count.SetLabel(self._count_text)
        self._model.SetForegroundColour(pal.text)
        self._port.SetForegroundColour(pal.muted)
        self._count.SetForegroundColour(pal.muted)
        self._msg.SetForegroundColour(pal.muted)
        message = self._message.strip() or _('Ready')
        self._msg.SetLabel(message)
        if self._model_text:
            colour = pal.connected if self._connected else pal.muted
        else:
            colour = pal.muted
        self._dot.SetForegroundColour(colour)
        self._dot.Show(bool(self._model_text))
        self.Layout()
