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
import vlc
# media_player = vlc.MediaPlayer()

ARGList = sys.argv[1:]
# Options
options = "hf:d"
long_options = ["Help", "file_konfig", "debug"]

DEBUG = False
Run = True
ALARM = False
MUSIC = False
# waktu_alarm = []
JAM_SEKARANG = time.strftime('%H:%M') #jam
NOW = datetime.datetime.now()
HARI_MASUK = []
PENGUMUMAN = ""
PLAYLIST_DIMAINKAN = "" # perintah untuk audio player
MUSIK_DIMAINKAN = ""

FILE_KONFIGURASI = "./config.json"
PENANDA_PLAYLIST = "PEMBUKA"
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


def get_playlist(playlist = ""):
    global DB_PLAYLIST
    if playlist in DB_PLAYLIST:
        return DB_PLAYLIST[playlist]
    else:
        return ""

def tts_to_mp3(teks = "", nama_file = "", bahasa = "id"):
    global DB_KONFIGURASI
    lokasi_file = DB_KONFIGURASI["lokasi_musik"]+"tts/"
    if not os.path.exists(lokasi_file):
        os.makedirs(lokasi_file)
    if DB_KONFIGURASI["kecepatan_pengejaan_tts"] == "tinggi":
        gtts_slow = False
    else:
        gtts_slow = True
    try:
        audio = gTTS(text=teks, lang=bahasa,slow=gtts_slow)
        audio.save(lokasi_file+nama_file)
        return True
    except Exception as err:
        print_log("Error pembacaan teks")
        return False

def music_player():
    # global media_player
    global DB_KONFIGURASI
    global Run, MUSIC, MUSIK_DIMAINKAN
    while Run:
        if MUSIK_DIMAINKAN != "" & MUSIC:
            playlist = get_playlist(MUSIK_DIMAINKAN)
            for musik in playlist:
                if not MUSIC:
                    break
                # media = vlc.Media(DB_KONFIGURASI['folder_musik']+musik)
                media_player = vlc.MediaPlayer(DB_KONFIGURASI['folder_musik']+musik)
                media_player.play()
                time.sleep(1)
                while media_player.is_playing() & MUSIC:
                    time.sleep(1)
                media_player.stop()
                time.sleep(0.5)
        time.sleep(0.5)

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
    global DB_KONFIGURASI, DB_PLAYLIST
    global Run, PLAYLIST_DIMAINKAN, MUSIK_DIMAINKAN
    print_log("Modul player dijalankan")
    while Run:
        if(PLAYLIST_DIMAINKAN != ""):
            nama_playlist = PLAYLIST_DIMAINKAN
            if nama_playlist.startwith(PENANDA_PLAYLIST):
                MUSIK_DIMAINKAN = nama_playlist
                # PLAYIST_DIMAINKAN = ""
            else:
                playing = get_playlist(PLAYLIST_DIMAINKAN)
                for play in playing:
                    play = DB_KONFIGURASI["folder_musik"]+play
                    if DEBUG:
                        print_log("playing "+play)
                    try:
                        playsound(play)
                    except Exception as error:
                        print_log("Gagal memainkan "+play)
                        print(error)
        PLAYLIST_DIMAINKAN = ""
        time.sleep(0.5)
    print_log("Modul player berhenti")

# untuk pengumuman menggunakan text to speech
def pengumuman():
    global Run, PENGUMUMAN, PLAYLIST_DIMAINKAN, DB_KONFIGURASI
    print_log("Modul pengumumang dijalankan")
    while Run:
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
    global JAM_SEKARANG, Run, PLAYLIST_DIMAINKAN, HARI_MASUK, ALARM, NOW
    if DEBUG:
        print(NOW.strftime("%d/%m/%Y"))
    # load_time()
    # if DEBUG:
    #     print("jam alarm : ", waktu_alarm)
    #     # print(waktu_alarm)
    print_log("Modul timer dijalankan")
    while Run:
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
            while ALARM & Run:
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
    print_log("Modul alarm berhenti")

# interface untuk debug
def interface():
    global thread_alarm, Run, PLAYLIST_DIMAINKAN, JAM_SEKARANG, ALARM, PENGUMUMAN
    print("\n")
    while Run:
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
            Run = False
            # return
            countdown = 60
            # print_log("menunggu roses berhenti")
            while (thread_alarm.is_alive() | thread_player.is_alive()) & countdown > 0:
                time.sleep(1)
            return
        else:
            print("Perintah tidak dikenali")
    Run = False

@http.route("/", methods=['GET', 'POST'])
def index():
    global PENGUMUMAN, DB_JADWAL, DB_PLAYLIST
    POST = '{}'
    if request.method == 'POST':
        POST = json.dumps(request.form)
        # print(request.form)
        if "isi" in request.form:
            PENGUMUMAN = request.form.get('isi')
        elif "jadwal" in request.form:
            jadwal = request.form.get('jadwal')
            file_conf = json.load(open(FILE_KONFIGURASI))
            file_conf['jadwal'] = json.loads(jadwal)
            DB_JADWAL = json.loads(jadwal)
            # print(json.dumps(file_conf, indent=4))
            with open(FILE_KONFIGURASI, 'w') as outfile:
                json.dump(file_conf, outfile, indent=4)
        elif "playlist" in request.form:
            playlist = request.form.get('playlist')
            file_conf = json.load(open(FILE_KONFIGURASI))
            file_conf['playlist'] = json.loads(playlist)
            DB_PLAYLIST = json.loads(playlist)
            # print(json.dumps(file_conf, indent=4))
            with open(FILE_KONFIGURASI, 'w') as outfile:
                json.dump(file_conf, outfile, indent=4)

    data = {"JADWAL":DB_JADWAL, "PLAYLIST":DB_PLAYLIST, "TANGGAL_LIBUR":DB_TANGGAL_LIBUR, "KONFIGURASI":DB_KONFIGURASI,"POST":json.loads(POST)}
    return render_template('index.html', data=data)

@http.route("/api/<string:page>/<string:key>", methods=['GET', 'POST'])
def api(page="",key=""):
    global DB_JADWAL, DB_KONFIGURASI, DB_PLAYLIST, DB_TANGGAL_LIBUR
    global http, Run, ALARM, PENGUMUMAN, NOW, HARI_MASUK,JAM_SEKARANG, PLAYLIST_DIMAINKAN, MUSIC

    response = ""
    if DB_KONFIGURASI['key_api']!= key:
        print_log("autentikasi gagal")
        return ""
    if request.method == "POST":
        post = True
    else:
        post = False
    

    if page == "pengumuman":
        if post:
            data = request.form.get('isi')
            # print(data)
            if(data == False):
                response = "pengumuman tidak valid"
            else:
                PENGUMUMAN = data
                response = PENGUMUMAN+" akan diumumkan"
    elif page == "info":
        informasi={}
        informasi['jam']=time.strftime('%H:%M')
        informasi['hari']=date_id()
        informasi['playlist_dimainkan']=PLAYLIST_DIMAINKAN
        informasi['thread_alarm']=thread_alarm.is_alive()
        informasi['thread_player']=thread_player.is_alive()
        informasi['thread_pengumuman']=thread_pengumuman.is_alive()
        informasi['status_timer']=ALARM
        response = jsonify(informasi)
    elif(page== "reload"):
        load_config()
        ALARM = False
        MUSIC = False
        response = ""
    elif page == "play":
        if post:
            playlist = request.form.get('playlist')
            if playlist in DB_PLAYLIST:
                PLAYLIST_DIMAINKAN = playlist
                response = ""
            else:
                err['stat'] = True
                err['pesan'] = "playlist tidak ditemukan"
                response = jsonify(err)
    elif page == "text2mp3":
        if post:
            text = request.form.get('text')
            nama_file = request.form.get('nama_file')
            if text != "" & nama_file != "":
                tts_to_mp3(text, nama_file)

    else:
        err["stat"] = True
        err["pesan"] = "404 not found"
        response = jsonify(err)
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
        # while Run:
        #     time.sleep(1)