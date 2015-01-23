import nest_thermostat as nest
import os
import twilio
import twilio.rest
from nest_thermostat import utils as nest_utils

import settings

class NestNotification:
    def __init__(self):
      self.client = twilio.rest.TwilioRestClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def send_notification(self, message):
        sent_message_count = 0

        try:
            for number in settings.TWILIO_TO_NUMBERS:
                print 'Notifying %s\n' % (number,)
                self.client.messages.create(
                    body=message,
                    to=number,
                    from_=settings.TWILIO_FROM_NUMBER
                )
            sent_message_count += 1
        except twilio.TwilioRestException as e:
            print e

        return sent_message_count

    def process(self):
        napi = nest.Nest(settings.NEST_USERNAME, settings.NEST_PASSWORD)

        sent_message_count = 0

        for structure in napi.structures:
            if structure.away:
                for device in structure.devices:
                    filename = device._serial
                    current_temp = nest_utils.c_to_f(device.temperature)
                    current_temp = int(round(current_temp))
                    away_temp = nest_utils.c_to_f(device._device.get('away_temperature_low'))
                    away_temp = int(round(away_temp))

                    # Notify if away temp is TRIGGER_TEMP_DIFF degrees above current
                    if (current_temp <= (away_temp - settings.TRIGGER_TEMP_DIFF)):
                        message = '%s (%s): Current temp is %sF, but it should be %sF' % (structure.name, device.name, current_temp, away_temp,)
                        print message

                        if os.path.exists(filename):
                            # Increment notification count
                            with open(filename, 'r') as f:
                                num_notifications = int(f.read()) + 1
                        else:
                            num_notifications = 1

                        # Write new notification count
                        with open(filename, 'w+') as f:
                            f.write(str(num_notifications))

                        if num_notifications <= settings.MAX_NOTIFICATIONS:
                            sent_message_count = self.send_notification(message)
                    else:
                        # Remove any existing notification files
                        if os.path.exists(filename):
                            message = '%s (%s): Temperature is now within expected range (current: %sF | set: %sF)' % (structure.name, device.name, current_temp, away_temp,)
                            sent_message_count = self.send_notification(message)
                            os.remove(filename)

                        message = '%s (%s): Temp OK\nCurrent: %sF | Set: %sF\n' % (structure.name, device.name, current_temp, away_temp,)

                        print message

        print 'Sent message count: %s' % (sent_message_count,)

if __name__ == '__main__':
    nest_notification = NestNotification()
    nest_notification.process()
