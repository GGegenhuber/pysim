# -*- coding: utf-8 -*-

""" pySim: PCSC reader transport link base
"""

import logging
from pySim.exceptions import *
from pySim.utils import sw_match

#
# Copyright (C) 2009-2010  Sylvain Munaut <tnt@246tNt.com>
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

class LinkBase(object):

	def wait_for_card(self, timeout=None, newcardonly=False):
		"""wait_for_card(): Wait for a card and connect to it

		   timeout     : Maximum wait time (None=no timeout)
		   newcardonly : Should we wait for a new card, or an already
				 inserted one ?
		"""
		pass

	def connect(self):
		"""connect(): Connect to a card immediately
		"""
		pass

	def disconnect(self):
		"""disconnect(): Disconnect from card
		"""
		pass

	def reset_card(self):
		"""reset_card(): Resets the card (power down/up)
		"""
		pass

	def send_apdu_raw(self, pdu):
		"""send_apdu_raw(pdu): Sends an APDU with minimal processing

		   pdu    : string of hexadecimal characters (ex. "A0A40000023F00")
		   return : tuple(data, sw), where
			    data : string (in hex) of returned data (ex. "074F4EFFFF")
			    sw   : string (in hex) of status word (ex. "9000")
		"""
		self.send_apdu_raw(pdu)

	def send_apdu_failsafe(self, pdu, retry_attempts = 5):
		"""send_apdu_failsafe(pdu): Sends an APDU with minimal processing and retries on error

		   pdu    : string of hexadecimal characters (ex. "A0A40000023F00")
		   return : tuple(data, sw), where
			    data : string (in hex) of returned data (ex. "074F4EFFFF")
			    sw   : string (in hex) of status word (ex. "9000")
		"""
		try:
			data, sw = self.send_apdu_raw(pdu)
			return data, sw
		except Exception as e1:
			if retry_attempts > 0:
				logging.info(f"eception occured when sending apdu {pdu}, retry...")
				return self.send_apdu_failsafe(pdu, retry_attempts-1)
			raise

	def send_apdu(self, pdu, retry_attempts = 0):
		"""send_apdu(pdu): Sends an APDU and auto fetch response data

		   pdu    : string of hexadecimal characters (ex. "A0A40000023F00")
		   return : tuple(data, sw), where
			    data : string (in hex) of returned data (ex. "074F4EFFFF")
			    sw   : string (in hex) of status word (ex. "9000")
		"""
		data, sw = self.send_apdu_failsafe(pdu, retry_attempts)
		# When whe have sent the first APDU, the SW may indicate that there are response bytes
		# available. There are two SWs commonly used for this 9fxx (sim) and 61xx (usim), where
		# xx is the number of response bytes available.
		# See also:
		# SW1=9F: 3GPP TS 51.011 9.4.1, Responses to commands which are correctly executed
		# SW1=61: ISO/IEC 7816-4, Table 5 — General meaning of the interindustry values of SW1-SW2
		if (sw is not None) and ((sw[0:2] == '9f') or (sw[0:2] == '61')):
			pdu_gr = pdu[0:2] + 'c00000' + sw[2:4]
			data, sw = self.send_apdu_failsafe(pdu_gr, retry_attempts)
		return data, sw

	def send_apdu_checksw(self, pdu, sw="9000"):
		"""send_apdu_checksw(pdu,sw): Sends an APDU and check returned SW

		   pdu    : string of hexadecimal characters (ex. "A0A40000023F00")
		   sw     : string of 4 hexadecimal characters (ex. "9000"). The
			    user may mask out certain digits using a '?' to add some
			    ambiguity if needed.
		   return : tuple(data, sw), where
			    data : string (in hex) of returned data (ex. "074F4EFFFF")
			    sw   : string (in hex) of status word (ex. "9000")
		"""
		rv = self.send_apdu(pdu)

		if not sw_match(rv[1], sw):
			raise SwMatchError(rv[1], sw.lower())
		return rv
