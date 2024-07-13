# kurang menjadikan penjadwalan dalam bentuk hari

import time
from playsound import playsound
import json
import threading
import icecast_client
import datetime


DEBUG = True
START = True
waktu_alarm = []
file_alarm = "alarm.json" #file database akan digantikan dengan mysql
Time = time.strftime('%H:%M') #jam
mainkan = "" # perintah untuk audio player
now = datetime.datetime.now()

file_konfigurasi = "./config.json"

playlist =[]
jadwal = []
konfig = []

def print_log(pesan):
    waktu = time.strftime('%b %d  %H:%M:%S ')
    pesan = waktu + pesan
    print(pesan)

# Hari dalam bahasa indonesia
def date_id(day=now.strftime("%A"),cap = False):
    day = day.lower()
    if day == "monday":
        day = "senin"
    elif day == "tuesday":
        day = "selasa"
    elif day == "wednesday":
        day = "rabu"
    elif day == "thursday":
        day = "kamis"
    elif day == "friday":
        day = "jumat"
    elif day == "saturday":
        day = "sabtu"
    elif day == "sunday":
        day = "minggu"
    else:
        day=""
    if cap:
        day = day.capitalize()
    return day

def load_config():
    global playlist, jadwal, konfig
    playlist.clear()
    jadwal.clear()
    konfig.clear()
    file = open(file_konfigurasi)
    try:
        data = json.load(file)
    except ValueError as err:
        print_log("Konfigurasi tidak bisa dibuka")
    else:
        print_log("mengupdate konfigurasi")
        playlist = data["playlist"]
        jadwal = data["jadwal"]
        konfig = data["konfigurasi"]
    if DEBUG:
        print(konfig)
        print(jadwal)
        print(playlist)
    file.close()

# ambil update schadule
def load_time():
    global waktu_alarm, jadwal
    if DEBUG:
        print_log("Updating schadule")
    waktu_alarm.clear()
    for k in jadwal:
        key = k
        waktu_alarm.append(key)

# Audio player
def player():
    global mainkan
    while START:
        if(mainkan != ""):
            if mainkan in playlist:
                playing = playlist[mainkan]
                for play in playing:
                    play = konfig["folder_musik"]+play
                    if DEBUG:
                        print_log("playing "+play)
                    playsound(play)
                    if DEBUG:
                        time.sleep(3)
            else:
                print_log("Playlist tidak ditemukan")
        mainkan = ""
    print_log("Player berhenti")

# Jam
def alarm():
    global waktu_alarm, Time, START, mainkan
    # load_time()
    if DEBUG:
        print("jam alarm : ", waktu_alarm)
        # print(waktu_alarm)
    while START:
        Time = time.strftime('%H:%M') 
        for alarm in waktu_alarm :
            if Time == alarm:
                if DEBUG:
                    print_log("Jam "+Time+" memulai playlist "+jadwal[alarm])
                # print("Jam : "+Time)
                # print("Memainkan : "+jadwal[alarm])
                mainkan = jadwal[alarm]
                time.sleep(59)
            # else:
                # if DEBUG:
        # print("Belum waktunya")
        time.sleep(1)
    # if DEBUG:
    #     print(waktu_alarm)
    print_log("proses alarm berhenti")

# interface untuk debug
def interface():
    global proses1, START, mainkan, Time
    print("\n")
    while START:
        perintah = input("Perintah: ")
        if(perintah== "reload"):
            # print("perintah 1")
            load_config()
            load_time()
        elif(perintah=="info"):
            print("Jadwal = ")
            print(waktu_alarm)
            print("Jam server = "+Time)
            print("Playlist saat ini : "+mainkan)
            print("status alarm : ",proses1.is_alive())
            print("status player : ",proses2.is_alive())
        elif(perintah=="play"):
            mainkan="bell"
        elif(perintah.lower() == "quit"):
            print_log("Mematikan proses")
            # if DEBUG:
            #     print("menghentikan proses")
            # proses1.join()
            START = False
            # return
            countdown = 60
            # print_log("menunggu roses berhenti")
            while (proses1.is_alive() | proses2.is_alive()) & countdown > 0:
                time.sleep(1)
            return
        else:
            print("Perintah tidak dikenali")
    START = False

if __name__ == "__main__":
    load_config()
    load_time()
    # print(waktu_alarm)
    proses1 = threading.Thread(target=alarm)
    proses2 = threading.Thread(target=player)
    proses1.daemon=True
    proses2.daemon=True
    proses1.start()
    proses2.start()
    #radio client
    if konfig["url_stream"] != "":
        icecast_client.init(konfig["url_stream"])
    if DEBUG:
        interface()
    else:
        while START:
            time.sleep(1)