# -----------------------------------------------------------------------------
# Copyright (c) 2022 Martin Schobert, Pentagrid AG
# Copyright (c) 2025 Riyan Firmansyah, Seclab Indonesia
#
# All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
#  ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  The views and conclusions contained in the software and documentation are those
#  of the authors and should not be interpreted as representing official policies,
#  either expressed or implied, of the project.
#
#  NON-MILITARY-USAGE CLAUSE
#  Redistribution and use in source and binary form for military use and
#  military research is not permitted. Infringement of these clauses may
#  result in publishing the source code of the utilizing applications and
#  libraries to the public. As this software is developed, tested and
#  reviewed by *international* volunteers, this clause shall not be refused
#  due to the matter of *national* security concerns.
# -----------------------------------------------------------------------------

import requests
import datetime
import logging
from email.mime.text import MIMEText
from typing import Tuple

from sms import SMS

class TelegramDelivery:
    def __init__(self, bot_token: str, health_check_interval: int) -> None:
        """
        Create a new TelegramDelivery object.
        This class handles the delivery of SMS via Telegram and it supports health checks.

        @param bot_token: The Telegram bot token.
        @param health_check_interval: The interval for the health check in seconds.
        """
        self.bot_token = bot_token
        self.health_check_interval = health_check_interval
        self.last_health_check = datetime.datetime.now()
        self.health_state = "OK"
        self.health_logs = None

        self.l = logging.getLogger("TelegramDelivery")

    def get_health_state(self) -> Tuple[str, str]:
        """
        Get the Telegram module's last measured health state.
        @return: The function returns a string tuple. The first element is either
            "OK", "WARNING" or "CRITICAL" and indicates the health state. The most severe level is reported. The
            second element is a string-concatenation of log messages or maybe an empty string if everything is okay.
        """
        return self.health_state, self.health_logs
    
    def do_health_check(self) -> Tuple[str, str]:
        """
        Check if a health check is necessary and potentially perform a health check.
        @return: The function returns a string tuple. The first element is either
            "OK", "WARNING" or "CRITICAL" and indicates the health state. The most severe level is reported. The
            second element is a string-concatenation of log messages or maybe an empty string if everything is okay.
        """
        now = datetime.datetime.now()
        if (now - self.last_health_check).total_seconds() >= self.health_check_interval:
            self.last_health_check = datetime.datetime.now()
            self.l.info("Collecting health check infos from Telegram server.")
            try:
                response = requests.get(f"https://api.telegram.org/bot{self.bot_token}/getMe")
                response.raise_for_status()
                self.health_state = "OK"
                self.health_logs = None
            except Exception as e:
                self.health_state = "CRITICAL"
                self.health_logs = f"Failed to get information from Telegram server: {e}"
        return self.health_state, self.health_logs
    
    def send_message(self, chat_id: str, message_thread_id: str, sms: SMS) -> bool:
        """
        Deliver an SMS as Telegram message.

        @param chat_id: The chat ID of the recipient.
        @param sms: A SMS object to send as Telegram message.
        @return: Returns True, if the message was delivered to the Telegram server and accepted. Returns False on error.
        """
        self.l.info(f"[{sms.get_id()}] Sending SMS as Telegram message to recipient {chat_id}.")
        try:
            message = sms.to_string()
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "message_thread_id": message_thread_id,
                    "text": message,
                    "link_preview_options": {"is_disabled": True}
                }
            )
            response.raise_for_status()
            self.l.info(f"[{sms.get_id()}] Sending Telegram message was successful.")
            self.health_state = "OK"
            self.health_logs = None
            return True
        except Exception as e:
            self.health_state = "CRITICAL"
            self.health_logs = f"Failed to send Telegram message: {e}"
            self.l.info(f"[{sms.get_id()}] Failed to send Telegram message: {e}")
