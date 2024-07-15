# kurang menjadikan penjadwalan dalam bentuk hari

import time
from playsound import playsound
import json
import threading
import icecast_client
import datetime
from gtts import gTTS
import os
import sys
from flask import Flask, render_template, redirect, request, jsonify
http =Flask(__name__)


DEBUG = False
RUN = True
ALARM = False
# waktu_alarm = []
HARI_MASUK = []
JAM_SEKARANG = time.strftime('%H:%M') #jam
PLAYLIST_DIMAINKAN = "" # perintah untuk audio player
NOW = datetime.datetime.now()
PENGUMUMAN = ""

FILE_KONFIGURASI = "./config-new.json"

DB_PLAYLIST =[]
DB_JADWAL = []
DB_KONFIGURASI = []
DB_TANGGAL_LIBUR = []

def print_log(pesan):
    waktu = time.strftime('%b %d  %H:%M:%S ')
    pesan = waktu + pesan
    print(pesan)

# Hari dalam bahasa indonesia
def date_id(day=NOW.strftime("%A"),cap = False):
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
    global DB_PLAYLIST, HARI_MASUK, DB_JADWAL, DB_KONFIGURASI, DB_TANGGAL_LIBUR

    file = open(FILE_KONFIGURASI)
    try:
        data = json.load(file)
    except ValueError as err:
        print_log("Konfigurasi tidak bisa dibuka")
    else:
        print_log("mengupdate konfigurasi")
        DB_PLAYLIST.clear()
        DB_PLAYLIST = data["playlist"]
        DB_JADWAL.clear()
        DB_JADWAL = data["jadwal"]
        DB_KONFIGURASI.clear()
        DB_KONFIGURASI = data["konfigurasi"]
        DB_TANGGAL_LIBUR.clear()
        DB_TANGGAL_LIBUR = data["tanggal_libur"]
    if DEBUG:
        print(DB_KONFIGURASI)
        print(DB_JADWAL)
        print(DB_PLAYLIST)
        print(DB_TANGGAL_LIBUR)
    file.close()
    for key in DB_JADWAL:
        hari = key
        HARI_MASUK.append(hari)
    if DEBUG:
        print(HARI_MASUK)

# ambil update schadule
def load_time(jadwal=[]):
    waktu_alarm=[]
    waktu_alarm.clear()
    for k in jadwal:
        key = k
        waktu_alarm.append(key)
    return waktu_alarm

# Audio player
def player():
    global PLAYLIST_DIMAINKAN
    while RUN:
        if(PLAYLIST_DIMAINKAN != ""):
            if PLAYLIST_DIMAINKAN in DB_PLAYLIST:
                playing = DB_PLAYLIST[PLAYLIST_DIMAINKAN]
                for play in playing:
                    play = DB_KONFIGURASI["folder_musik"]+play
                    if DEBUG:
                        print_log("playing "+play)
                    playsound(play)
                    # if DEBUG:
                    #     time.sleep(3)
            else:
                print_log("Playlist tidak ditemukan")
        PLAYLIST_DIMAINKAN = ""
    print_log("Player berhenti")

# untuk pengumuman menggunakan text to speech
def pengumuman():
    global RUN, PENGUMUMAN, PLAYLIST_DIMAINKAN, DB_KONFIGURASI
    while RUN:
        if PENGUMUMAN != "":
                if os.path.isfile("output.mp3"):
                    os.remove("output.mp3")
                print_log("Mengumumkan "+PENGUMUMAN)
                try:
                    res = gTTS(text=PENGUMUMAN, lang='id', slow=False)
                    filename = "output.mp3"
                    res.save(filename)
                    # tunggu jika masih ada yang dimainkan
                    if DB_KONFIGURASI["tunggu_playlist_selesai"] == "Ya" :
                        while PLAYLIST_DIMAINKAN != "":
                            time.sleep(1)
                    if DB_KONFIGURASI["nada_pemberitahuan"] != "":
                        playsound(DB_KONFIGURASI["folder_musik"]+DB_KONFIGURASI["nada_pemberitahuan"])
                    playsound("output.mp3")
                except Exception as e:
                    print_log("Pengumuman gagal")
                    print(e)
                PENGUMUMAN = ""

    time.sleep(1)

# Jam
# konsep baru
# dalam pengecekan looping, akan dilakukan looping kedua,
# dimana looping kedua akan melakukan looping selama setatus ALARM True, sedangkan looping utama akan sesuai dengan status program
# status alarm akan dirubah sesuai dengan hari yang akan dicek oleh looping utama dan dicek oleh looping alarm
# dalam pengecekan di looping alarm, akadn dicek apakah hari ini masih sama dengan hari yang dijalankan
# dalam pengecekkan looping utama akan dicek apakah hari ini libur atau tidak 
def alarm():
    global JAM_SEKARANG, RUN, PLAYLIST_DIMAINKAN, HARI_MASUK, ALARM, NOW
    if DEBUG:
        print(NOW.strftime("%d/%m/%Y"))
    # load_time()
    # if DEBUG:
    #     print("jam alarm : ", waktu_alarm)
    #     # print(waktu_alarm)
    while RUN:
        ALARM = False
        hari_ini = date_id()
        NOW = datetime.datetime.now()
        tanggal = NOW.strftime("%d/%m/%Y")
        
        #pengecekkan hari libur
        for hari in HARI_MASUK:
            if hari == hari_ini:
                #pengecekkan tanggal libur
                for tgl in DB_TANGGAL_LIBUR:
                    # print(tgl)
                    ALARM = True
                    if tgl == tanggal:
                        ALARM = False
                # time.sleep(100)
        #perulangan yang baru
        if ALARM:
            while ALARM & RUN:
                jam_alarm = load_time(DB_JADWAL[hari_ini])
                JAM_SEKARANG = time.strftime('%H:%M')
                for alarm in jam_alarm:
                    if JAM_SEKARANG == alarm:
                        PLAYLIST_DIMAINKAN = DB_JADWAL[hari_ini][JAM_SEKARANG]
                        print_log("Memainkan playlist "+PLAYLIST_DIMAINKAN)
                        time.sleep(59)
                #cek apakah sudah berganti hari
                time.sleep(1)
                if(hari_ini != date_id()):
                    ALARM=False
                    print_log("Perhantian hari jadwal direset!")
        else:
            time.sleep(60)
        # JAM_SEKARANG = time.strftime('%H:%M') 
        # for hari in HARI_MASUK:
        #     if hari == hari_ini:
        #         ALARM = True
        #         jam_alarm = load_time(DB_JADWAL[hari])
        #         # print(jam_alarm)
        #         for alarm in jam_alarm :
        #             if JAM_SEKARANG == alarm:
        #                 DB_PLAYLIST=DB_JADWAL[hari][alarm]
        #                 if DEBUG:
        #                     print_log("Jam "+JAM_SEKARANG+" memulai DB_PLAYLIST "+DB_PLAYLIST)
        #                 # print (DB_JADWAL[hari][alarm])
        #                 PLAYLIST_DIMAINKAN = DB_PLAYLIST
        #                 time.sleep(59)
        #     else:
        #         ALARM = False
        # time.sleep(600)
    # if DEBUG:
    #     print(waktu_alarm)
    print_log("proses alarm berhenti")

# interface untuk debug
def interface():
    global thread_alarm, RUN, PLAYLIST_DIMAINKAN, JAM_SEKARANG, ALARM, PENGUMUMAN
    print("\n")
    while RUN:
        perintah = input("Perintah: ")
        if(perintah== "reload"):
            # print("perintah 1")
            load_config()
            ALARM=False
            # load_time()
        elif(perintah=="info"):
            # print("Jadwal : ")
            # print(DB_JADWAL[date_id()])
            print("Jam server           : ",time.strftime('%H:%M'))
            print("Hari                 : ",date_id())
            print("Playlist saat ini    : ",PLAYLIST_DIMAINKAN)
            print("status thread alarm  : ",thread_alarm.is_alive())
            print("status thread player : ",thread_player.is_alive())
            print("Alarm berjalan       : ",ALARM)
        elif(perintah=="pengumuman"):
            PENGUMUMAN=input("Pengumuman : ")
        elif(perintah=="play"):
            PLAYLIST_DIMAINKAN="bell"
        elif(perintah.lower() == "quit"):
            print_log("Mematikan proses")
            # if DEBUG:
            #     print("menghentikan proses")
            # thread_alarm.join()
            RUN = False
            # return
            countdown = 60
            # print_log("menunggu roses berhenti")
            while (thread_alarm.is_alive() | thread_player.is_alive()) & countdown > 0:
                time.sleep(1)
            return
        else:
            print("Perintah tidak dikenali")
    RUN = False

@http.route("/")
def index():
    return "Hello"

@http.route("/api/<string:page>/<string:key>", methods=['GET', 'POST'])
def api(page="",key=""):
    global DB_JADWAL, DB_KONFIGURASI, DB_PLAYLIST, DB_TANGGAL_LIBUR
    global http, RUN, ALARM, PENGUMUMAN, NOW, HARI_MASUK,JAM_SEKARANG, PLAYLIST_DIMAINKAN
    response = ""
    if DB_KONFIGURASI['key_api']!= key:
        print_log("autentikasi gagal")
        return ""
    else:
        if(request.method == "POST"):
            if page == "pengumuman":
                data = request.form.get('isi')
                # print(data)
                if(data == False):
                    return "pengumuman tidak valid"
                else:
                    PENGUMUMAN = data
                    return PENGUMUMAN+" akan diumumkan"
            # elif page == "restart":
            #     data = request.form.get('thread')
            #     if data == False:
            #         return ""
            #     else:
            #         if data == "pengumuman":
            #             if not thread_pengumuman.is_alive():
            #                 thread_pengumuman.start()
            #                 return "thread pengumuman direstart"
                # RUN = False
                # thread_alarm.join()
                # thread_player.join()
                # thread_pengumuman.join()
                # while thread_alarm.is_alive() | thread_player.is_alive() | thread_pengumuman.is_alive():
                #     time.sleep(1)
                # thread_alarm.start()
                # thread_player.start()
                # thread_pengumuman.start()
                # os.execl(sys.executable, os.path.abspath(__file__), *sys.argv) 
                # return "restarted"
            else:
                return ""
        elif request.method == "GET":
            if(page== "reload"):
                # print("perintah 1")
                load_config()
                ALARM=False
                # load_time()
            elif(page=="info"):
                # print("Jadwal : ")
                # print(DB_JADWAL[date_id()])
                informasi={}
                informasi['jam']=time.strftime('%H:%M')
                informasi['hari']=date_id()
                informasi['playlist_dimainkan']=PLAYLIST_DIMAINKAN
                informasi['thread_alarm']=thread_alarm.is_alive()
                informasi['thread_player']=thread_player.is_alive()
                informasi['thread_pengumuman']=thread_pengumuman.is_alive()
                informasi['status_timer']=ALARM
                return jsonify(informasi)
                
                # print("Jam server           : ",time.strftime('%H:%M'))
                # print("Hari                 : ",date_id())
                # print("Playlist saat ini    : ",PLAYLIST_DIMAINKAN)
                # print("status thread alarm  : ",thread_alarm.is_alive())
                # print("status thread player : ",thread_player.is_alive())
                # print("Alarm berjalan       : ",ALARM)
            elif(page=="pengumuman"):
                PENGUMUMAN=input("Pengumuman : ")
            elif(page=="play"):
                PLAYLIST_DIMAINKAN="bell"
            elif(page.lower() == "quit"):
                print_log("Mematikan proses")
                RUN = False
            else:
                return ""
    return response


if __name__ == "__main__":
    load_config()

    # print(waktu_alarm)
    thread_alarm = threading.Thread(target=alarm, daemon=True)
    thread_player = threading.Thread(target=player, daemon=True)
    thread_pengumuman = threading.Thread(target=pengumuman, daemon=True)
    thread_alarm.start()
    thread_player.start()
    thread_pengumuman.start()
    #radio client
    if DB_KONFIGURASI["url_stream"] != "":
        icecast_client.init(DB_KONFIGURASI["url_stream"])
    if DEBUG:
        interface()
    else:
        http.run(debug=True)
        # while RUN:
        #     time.sleep(1)