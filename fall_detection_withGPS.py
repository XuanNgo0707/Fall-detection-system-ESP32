from machine import SoftI2C, Pin, sleep, UART
import mpu6050
import math
import time
import network
import BlynkLib
import network
import machine
import umail
import utime
gpsModule = UART(2, baudrate=9600)
print(gpsModule)
# gian gia tri thong so gps
buff = bytearray(255)

TIMEOUT = False
FIX_STATUS = False

latitude = 10000
longitude = 10000
satellites = ""
GPStime = ""

#kết nối wifi
wifi_ssid = 'ip11'
wifi_password = '1234567899'
def connect_to_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        pass
    print('Đã kết nối với mạng Wi-Fi')
    print('Địa chỉ IP:', wlan.ifconfig()[0])
connect_to_wifi(wifi_ssid, wifi_password)

BLYNK_AUTH = "Rz1rthVpUwS-giN-P9usCw-PePHXgm-B"
blynk = BlynkLib.Blynk(BLYNK_AUTH)
#điện áp chân 5 ở mức cao
v5 = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)

coibao = Pin(2, Pin.OUT)
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
accelerometer = mpu6050.accel(i2c)
#coibaodong
def update_blynk_status(value):
    blynk.virtual_write(0, value)
@blynk.on("V0") #virtual pin V0
def v0_read_handler(value): #read the value
	if int(value[0]) == 0: 
		coibao.value(0) #tat coi bao
	else:
		coibao.value(1) #bat coi bao
#gưi email
sender_email='lehoangchinh1111@gmail.com'
sender_name='ESP32'
sender_app_password='dbcz muek qaxl ahxr'
recipient_email='hoangchinh38a1111@gmail.com'
#Hàm gửi email
def send_email(sender_email, sender_name, sender_app_password, recipient_email, email_subject, email_message):
    try:
        smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True)  # Gmail's SSL port
        smtp.login(sender_email, sender_app_password)
        smtp.to(recipient_email)
        smtp.write("From:" + sender_name + "<" + sender_email + ">\n")
        smtp.write("Subject:" + email_subject + "\n")
        smtp.write("Content-Type: text/html\n")  # Đặt kiểu nội dung là HTML
        smtp.write("\n")
        smtp.write(email_message)
        smtp.send()
        smtp.quit()
        print('Email sent successfully')
    except Exception as e:
        print(f'Failed to send email: {e}')
fall = False
trigger1 = False
trigger2 = False
trigger3 = False
trigger1count = 0
trigger2count = 0
trigger3count = 0
# ham gps
def getGPS(gpsModule):
    global FIX_STATUS, TIMEOUT, latitude, longitude, satellites, GPStime
    
    timeout = time.time() + 8 
    while True:
        gpsModule.readline()
        buff = str(gpsModule.readline())
        parts = buff.split(',')
    
        if (parts[0] == "b'$GPGGA" and len(parts) == 15):
            if(parts[1] and parts[2] and parts[3] and parts[4] and parts[5] and parts[6] and parts[7]):
                print(buff)
                
                latitude = convertToDegree(parts[2])
                if (parts[3] == 'S'):
                    latitude = -latitude
                longitude = convertToDegree(parts[4])
                if (parts[5] == 'W'):
                    longitude = -longitude
                satellites = parts[7]
                GPStime = parts[1][0:2] + ":" + parts[1][2:4] + ":" + parts[1][4:6]
                FIX_STATUS = True
                break
                
        if (time.time() > timeout):
            TIMEOUT = True
            break
        utime.sleep_ms(500)
        
def convertToDegree(RawDegrees):

    RawAsFloat = float(RawDegrees)
    firstdigits = int(RawAsFloat/100) 
    nexttwodigits = RawAsFloat - float(firstdigits*100) 
    
    Converted = float(firstdigits + nexttwodigits/60.0)
    Converted = '{0:.6f}'.format(Converted) 
    return str(Converted)
while True:
    blynk.run()
    #nutkhancap  
    if v5.value() == 0: #điện áp chân 5 bằng 0
        blynk.log_event("cau_cuu")#sự kiện cau_cuu trên Blynk được diễn ra 
        email_subject = 'He thong canh bao nga'
        getGPS(gpsModule)
        print(latitude)
        print(longitude)
        email_message = '<a href="https://www.google.com/maps/place/' + str(latitude) + ',' + str(longitude) + '">Liên kết Google Maps</a>'
        send_email(sender_email, sender_name, sender_app_password, recipient_email,
        email_subject,
        email_message
    )
    
    #đọc và hiệu chỉnh giá trị cảm biến
    sensor_values = accelerometer.get_values()
    ax = (sensor_values['AcX'] - 2050) / 16384.00
    ay = (sensor_values['AcY'] - 77) / 16384.00
    az = (sensor_values['AcZ'] - 1947) / 16384.00
    gx = (sensor_values['GyX'] + 270) / 131.07
    gy = (sensor_values['GyY'] - 351) / 131.07
    gz = (sensor_values['GyZ'] + 136) / 131.07
    
    #thuật toán phát hiện té ngă
    Raw_Amp = math.sqrt(ax**2 + ay**2 + az**2)
    Amp = Raw_Amp * 10
    print(f'GIA TỐC HƯỚNG: {Amp:.2f}')
    if Amp <= 3 and not trigger2:
        trigger1 = True
        print("TRIGGER 1 ACTIVATED")
    if trigger1:
        trigger1count += 1
        if Amp >= 6:
            trigger2 = True
            print("TRIGGER 2 ACTIVATED")
            trigger1 = False
            trigger1count = 0
    if trigger2:
        trigger2count += 1
        angleChange = math.sqrt(gx**2 + gy**2 + gz**2)
        print(f'GIA TỐC GÓC: {angleChange:.2f}')
        if 50 <= angleChange <= 450:
            trigger3 = True
            trigger2 = False
            trigger2count = 0
            print(f'GIA TỐC GÓC: {angleChange:.2f}')
            print("TRIGGER 3 ACTIVATED")
    if trigger3:
        trigger3count += 1
        if trigger3count >= 4:
            angleChange = math.sqrt(gx**2 + gy**2 + gz**2)
            print(f'GIA TỐC GÓC: {angleChange:.2f}')
            if 0 <= angleChange <= 100:
                fall = True
                trigger3 = False
                trigger3count = 0
                print(f'GIA TỐC GÓC: {angleChange:.2f}')
            else:
                trigger3 = False
                trigger3count = 0
                print("TRIGGER 3 DEACTIVATED")
    if fall:
        print("FALL DETECTED")
        blynk.log_event("te_nga");#sự kiện te_nga trên Blynk được diễn ra 
        coibao.value(1);#bật c̣oi báo
        update_blynk_status(1)
        getGPS(gpsModule)
        print(latitude)
        print(longitude)
        email_subject = 'He thong canh bao nga'
        email_message = '<a href="https://www.google.com/maps/place/' + str(latitude) + ',' + str(longitude) + '">Liên kết Google Maps</a>'
        send_email(sender_email, sender_name, sender_app_password, recipient_email,
        email_subject,
        email_message
    )
        fall = False
    if trigger2count >= 6:
        trigger2 = False
        trigger2count = 0
        print("TRIGGER 2 DEACTIVATED")
    if trigger1count >= 6:
        trigger1 = False
        trigger1count = 0
        print("TRIGGER 1 DEACTIVATED")

    
    time.sleep(0.1)





