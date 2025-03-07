# -*- coding: utf-8 -*-

# Copyright (C) 2009-2010  Sylvain Munaut <tnt@246tNt.com>
# Copyright (C) 2010  Harald Welte <laforge@gnumonks.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from smartcard.CardConnection import CardConnection
from smartcard.CardRequest import CardRequest
from smartcard.Exceptions import NoCardException, CardRequestTimeoutException, CardConnectionException, CardConnectionException
from smartcard.System import readers

from pySim.exceptions import NoCardError, ProtocolError, ReaderError
from pySim.transport import LinkBase
from pySim.utils import h2i, i2h


class PcscSimLink(LinkBase):
	""" pySim: PCSC reader transport link."""

	def __init__(self, reader_number:int=0, protocol=None, **kwargs):
		super().__init__(**kwargs)
		r = readers()
		if reader_number >= len(r):
			raise ReaderError
		self._protocol = protocol # CardConnection.T0_protocol || CardConnection.T1_protocol || CardConnection.RAW_protocol
		self._reader = r[reader_number]
		self._con = self._reader.createConnection()

	def __del__(self):
		try:
			# FIXME: this causes multiple warnings in Python 3.5.3
			self._con.disconnect()
		except:
			pass
		return

	def wait_for_card(self, timeout:int=None, newcardonly:bool=False):
		cr = CardRequest(readers=[self._reader], timeout=timeout, newcardonly=newcardonly)
		try:
			cr.waitforcard()
		except CardRequestTimeoutException:
			raise NoCardError()
		self.connect()

	def connect(self):
		try:
			# To avoid leakage of resources, make sure the reader
			# is disconnected
			self.disconnect()

			# https://github.com/LudovicRousseau/pyscard/blob/master/smartcard/pcsc/PCSCCardConnection.py#L95
			self._con.connect(protocol = self._protocol)
		except CardConnectionException:
			raise ProtocolError()
		except NoCardException:
			raise NoCardError()

	def get_atr(self):
		return bytes(self._con.getATR())

	def disconnect(self):
		self._con.disconnect()

	def reset_card(self):
		self.disconnect()
		self.connect()
		return 1

	def _send_apdu_raw(self, pdu):

		apdu = h2i(pdu)

		data, sw1, sw2 = self._con.transmit(apdu)

		sw = [sw1, sw2]

		# Return value
		return i2h(data), i2h(sw)
