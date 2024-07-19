# kurang menjadikan penjadwalan dalam bentuk hari

import time
from playsound import playsound
import json
import threading
# import icecast_client
import datetime
from gtts import gTTS
import os
import sys, getopt
from flask import Flask, render_template, redirect, request, jsonify
http =Flask(__name__)

ARGList = sys.argv[1:]
# Options
options = "hf:d"
long_options = ["Help", "file_konfig", "debug"]

DEBUG = False
RUN = True
ALARM = False
# waktu_alarm = []
HARI_MASUK = []
JAM_SEKARANG = time.strftime('%H:%M') #jam
PLAYLIST_DIMAINKAN = "" # perintah untuk audio player
NOW = datetime.datetime.now()
PENGUMUMAN = ""

FILE_KONFIGURASI = "./config.json"

DB_PLAYLIST =[]
DB_JADWAL = []
DB_KONFIGURASI = []
DB_TANGGAL_LIBUR = []

def print_log(pesan):
    waktu = time.strftime('[%b %d  %H:%M:%S] ')
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
        print(err)
    else:
        print_log("Mengupdate konfigurasi")
        DB_PLAYLIST.clear()
        DB_PLAYLIST = data["playlist"]
        DB_JADWAL.clear()
        DB_JADWAL = data["jadwal"]
        DB_KONFIGURASI.clear()
        DB_KONFIGURASI = data["konfigurasi"]
        DB_TANGGAL_LIBUR.clear()
        DB_TANGGAL_LIBUR = data["tanggal_libur"]
    if DEBUG:
        print("\nKonfigurasi :")
        print(DB_KONFIGURASI)
        print("\nJadwal :")
        print(DB_JADWAL)
        print("\nPlaylist :")
        print(DB_PLAYLIST)
        print("\nTanggal libur :")
        print(DB_TANGGAL_LIBUR)
        print("\n")
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
    print_log("Modul player dijalankan")
    while RUN:
        if(PLAYLIST_DIMAINKAN != ""):
            if PLAYLIST_DIMAINKAN in DB_PLAYLIST:
                playing = DB_PLAYLIST[PLAYLIST_DIMAINKAN]
                for play in playing:
                    play = DB_KONFIGURASI["folder_musik"]+play
                    if DEBUG:
                        print_log("playing "+play)
                    try:
                        playsound(play)
                    except Exception as error:
                        print_log("Gagal memainkan "+play)
                        print(error)
            else:
                print_log("Playlist tidak ditemukan")
        PLAYLIST_DIMAINKAN = ""
    print_log("Modul player berhenti")
    time.sleep(0.5)

# untuk pengumuman menggunakan text to speech
def pengumuman():
    global RUN, PENGUMUMAN, PLAYLIST_DIMAINKAN, DB_KONFIGURASI
    print_log("Modul pengumumang dijalankan")
    while RUN:
        if PENGUMUMAN != "":
                if os.path.isfile("output.mp3"):
                    os.remove("output.mp3")
                print_log("Mengumumkan "+PENGUMUMAN)
                try:
                    if DB_KONFIGURASI["kecepatan_pengejaan_tts"] == "tinggi":
                        gtts_slow = False
                    else:
                        gtts_slow = True
                    res = gTTS(text=PENGUMUMAN, lang='id', slow=gtts_slow)
                    filename = "output.mp3"
                    res.save(filename)
                    # tunggu jika masih ada yang dimainkan
                    if DB_KONFIGURASI["tunggu_playlist_selesai"] == "Ya" :
                        while PLAYLIST_DIMAINKAN != "":
                            time.sleep(1)
                    try:
                        if DB_KONFIGURASI["nada_pemberitahuan"] != "":
                            playsound(DB_KONFIGURASI["folder_musik"]+DB_KONFIGURASI["nada_pemberitahuan"])
                        playsound("output.mp3")
                    except Exception as error:
                        print_log("Gagal memainkan audio")
                        print(error)
                except Exception as e:
                    print_log("Pengumuman gagal")
                    print(e)
                PENGUMUMAN = ""
        time.sleep(1)
    print_log("Modul pengumuman berhenti")
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
    print_log("Modul timer dijalankan")
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
    print_log("Modul alarm berhenti")

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

@http.route("/", methods=['GET', 'POST'])
def index():
    global PENGUMUMAN
    if request.method == 'POST':
        data = request.form.get('isi')
        if data != False:
            PENGUMUMAN = data
    data = {"JADWAL":DB_JADWAL, "PLAYLIST":DB_PLAYLIST, "TANGGAL_LIBUR":DB_TANGGAL_LIBUR, "KONFIGURASI":DB_KONFIGURASI}
    return render_template('index.html', data=data)

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
            else:
                return ""
        elif request.method == "GET":
            if(page== "reload"):
                load_config()
                ALARM=False
            elif(page=="info"):
                informasi={}
                informasi['jam']=time.strftime('%H:%M')
                informasi['hari']=date_id()
                informasi['playlist_dimainkan']=PLAYLIST_DIMAINKAN
                informasi['thread_alarm']=thread_alarm.is_alive()
                informasi['thread_player']=thread_player.is_alive()
                informasi['thread_pengumuman']=thread_pengumuman.is_alive()
                informasi['status_timer']=ALARM
                return jsonify(informasi)
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
    try:
        arguments, values = getopt.getopt(ARGList, options, long_options)
        for currentArgument, currentValue in arguments:
            if currentArgument in ("-h", "--Help"):
                print("help")
                sys.exit()
            elif currentArgument in ("-f", "--file_konfig"):
                FILE_KONFIGURASI = currentValue
                print_log("Menggunakan file konfigurasi di "+FILE_KONFIGURASI)
            elif currentArgument in ("-d", "--debug"):
                DEBUG = True
    except getopt.error as err:
        print(str(err))
        sys.exit()
    load_config()

    # print(waktu_alarm)
    thread_alarm = threading.Thread(target=alarm, daemon=True)
    thread_player = threading.Thread(target=player, daemon=True)
    thread_pengumuman = threading.Thread(target=pengumuman, daemon=True)
    thread_alarm.start()
    thread_player.start()
    thread_pengumuman.start()
    #radio client
    # if DB_KONFIGURASI["url_stream"] != "":
    #     icecast_client.init(DB_KONFIGURASI["url_stream"])
    # if DEVELOP:
    #     interface()
    # else:
    http.run(debug=DEBUG,host=DB_KONFIGURASI['listen'],port=DB_KONFIGURASI['port'])
        # while RUN:
        #     time.sleep(1)