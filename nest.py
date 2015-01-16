import nest_thermostat as nest
import twilio
import twilio.rest
from nest_thermostat import utils as nest_utils

from settings import *

# Temperature difference (in degrees F) after which to send notification
TRIGGER_TEMP_DIFF = 3

def main():
    sent_message_count = 0

    client = twilio.rest.TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    napi = nest.Nest(NEST_USERNAME, NEST_PASSWORD)

    for structure in napi.structures:
        if structure.away:
            for device in structure.devices:
                current_temp = nest_utils.c_to_f(device.temperature)
                current_temp = int(round(current_temp))
                away_temp = nest_utils.c_to_f(device._device.get('away_temperature_low'))
                away_temp = int(round(away_temp))

                # Notify if away temp is TRIGGER_TEMP_DIFF degrees above current
                if (current_temp <= (away_temp - TRIGGER_TEMP_DIFF)):
                    message = '%s (%s): Current temp is %sF, but it should be %sF' % (structure.name, device.name, current_temp, away_temp,)

                    try:
                        message = client.messages.create(
                            body = message,
                            to='+16034900078',
                            from_='+14155992671'
                        )
                        sent_message_count += 1
                    except twilio.TwilioRestException as e:
                        print e
                else:
                    message = '%s (%s): Temp OK\nCurrent: %sF | Set: %sF\n' % (structure.name, device.name, current_temp, away_temp,)

                    print message

    print 'Sent message count: %s' % (sent_message_count,)

if __name__ == '__main__':
    main()
