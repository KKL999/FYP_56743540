import cv2
import numpy as np
import schedule,time
import pymysql
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess

lock = threading.Lock()

seconds = time.time()

local_time = time.ctime(seconds)

last_execution_time = 0

#Set the database credentials
host = 'database-1.ccrc03jeprkh.us-east-1.rds.amazonaws.com'
port = 3306
user = 'hflui7'
password = '56743540'
database= 'Camera1_schema'

    #Connect to the database
connection = pymysql.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    database=database
         )

def detect():
    #'C:/Users/user/Desktop/FYP/Produce2.mp4'

    # Turn on the web camera
    cap = cv2.VideoCapture('C:/Users/user/Desktop/FYP/Produce2.mp4')

    # Set image size
    width = 1280
    height = 960

    # Set the size of the captured image
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # Calculate screen area
    area = width * height

    # Initialize average image
    ret, frame = cap.read()
    avg = cv2.blur(frame, (4, 4))
    avg_float = np.float32(avg)
    count = 0

    while(cap.isOpened()):
        # read a frame
        ret, frame = cap.read()

        # If it is read to the end of the video, it will jump out.
        if ret == False:
            break

        # blurring
        blur = cv2.blur(frame, (4, 4))

        # Calculate the difference between the current frame and the average image
        diff = cv2.absdiff(avg, blur)

        # Convert image to grayscale
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

        # Filter out areas with changes greater than the threshold
        ret, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)

        # Use type conversion functions to remove noise
        kernel = np.ones((5, 5), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

        # generate contour lines
        cnts,cntImg = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        seconds = time.time()

        local_time = time.ctime(seconds)

        currentTime= int(time.strftime('%H'))

        for c in cnts:
            # Ignore areas that are too small
            if cv2.contourArea(c) < 500:
                continue

            # Calculate the contour range of the contour line
            (x, y, w, h) = cv2.boundingRect(c)

            # draw outline
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            print('detected')

            print(count)

            if currentTime > 100 and currentTime < 101:
                msg = MIMEMultipart()
                msg['From'] = 'kklprometheus@gmail.com'
                msg['To'] = 'kklprometheus@gmail.com'
                msg['Subject'] = 'Motion Detected on uncommon time'

                message = local_time
                msg.attach(MIMEText('Your Camera had captured motion on uncommon Time:' + message))
                mailserver = smtplib.SMTP('smtp.gmail.com',587)
                                # identify ourselves to smtp gmail client
                mailserver.ehlo()
                                # secure our email with tls encryption
                mailserver.starttls()
                                # re-identify ourselves as an encrypted connection
                mailserver.ehlo()
                mailserver.login('kklprometheus@gmail.com', 'ikzn xcmw ibxs mzlk')
                mailserver.sendmail('kklprometheus@gmail.com','kklprometheus@gmail.com',msg.as_string())
                mailserver.quit()
                
            if count >= 50:
                count = count - 50

                print(count)

                # Create a cursor object
                cursor = connection.cursor()
                
                # Write the SQL query to update the table
                sql_query = "INSERT INTO Camera1_Detect VALUES (%s, %s);"
                values = ('Motion Detected', local_time)

                # Execute the SQL query
                lock.acquire()

                cursor.execute(sql_query, values)

                # Commit the changes to the database
                connection.commit()

                lock.release()
                
                
            count= count + 1
            print(count)
            
        # Display detection result image
        cv2.imshow('Camera1', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Update average image
        cv2.accumulateWeighted(blur, avg_float, 0.01)
        avg = cv2.convertScaleAbs(avg_float)

    cap.release()
    cv2.destroyAllWindows()

def heartbeat():


    # Create a cursor object
    cursor = connection.cursor()
        
    def job():
        print('Alive')

        seconds = time.time()
        
        local_time = time.ctime(seconds)
        
        # Write the SQL query to update the table
        sql_query = "INSERT INTO Camera1_Status VALUES (%s, %s);"
        values = ('Camera1 Alive', local_time)

        # Execute the SQL query
        lock.acquire()
        cursor.execute(sql_query, values)
        # Commit the changes to the database
        connection.commit()
        lock.release()

    schedule.every(20).seconds.do(job)
    while True:
        schedule.run_pending()
        
two=threading.Thread(target=detect)
three=threading.Thread(target=heartbeat)
two.start()
three.start()
for i in range(1):
    print("CAMERA STARTED")
two.join()