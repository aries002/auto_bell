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
Alarm = False
Music = False
# waktu_alarm = []
jam_sekarang = time.strftime('%H:%M') #jam
Now = datetime.datetime.now()
Hari_masuk = []
Pengumuman = ""
Bell_dimainkan = "" # perintah untuk audio player
Musik_dimainkan = ""

FILE_KONFIGURASI = "./config.json"
PENANDA_PLAYLIST = "PEMBUKA"
DB_playlist =[]
DB_jadwal = []
DB_konfigurasi = []
DB_libur = []

def print_log(pesan):
    waktu = time.strftime('\n[%b %d  %H:%M:%S] ')
    pesan = waktu + pesan
    print(pesan)

# def config2file():
#     global DB_jadwal, DB_konfigurasi, DB_libur, DB_playlist
#     global FILE_KONFIGURASI

# Hari dalam bahasa indonesia
def date_id(day=Now.strftime("%A"),cap = False):
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
    global DB_playlist, Hari_masuk, DB_jadwal, DB_konfigurasi, DB_libur

    file = open(FILE_KONFIGURASI)
    try:
        data = json.load(file)
    except ValueError as err:
        print_log("Konfigurasi tidak bisa dibuka")
        print(err)
    else:
        print_log("Mengupdate konfigurasi")
        DB_playlist.clear()
        DB_playlist = data["playlist"]
        DB_jadwal.clear()
        DB_jadwal = data["jadwal"]
        DB_konfigurasi.clear()
        DB_konfigurasi = data["konfigurasi"]
        DB_libur.clear()
        DB_libur = data["tanggal_libur"]
    if DEBUG:
        print("\nKonfigurasi :")
        print(DB_konfigurasi)
        print("\nJadwal :")
        print(DB_jadwal)
        print("\nPlaylist :")
        print(DB_playlist)
        print("\nTanggal libur :")
        print(DB_libur)
        print("\n")
    file.close()
    for key in DB_jadwal:
        hari = key
        Hari_masuk.append(hari)
    if DEBUG:
        print(Hari_masuk)

def get_playlist(playlist = ""):
    global DB_playlist
    if playlist in DB_playlist:
        return DB_playlist[playlist]
    else:
        return ""

def tts_to_mp3(teks = "", nama_file = "", bahasa = "id", overwrite = True):
    global DB_konfigurasi
    lokasi_file = DB_konfigurasi["folder_musik"]+"tts/"
    if not os.path.exists(lokasi_file):
        os.makedirs(lokasi_file)
    if os.path.isfile(lokasi_file+nama_file):
        if overwrite:
            os.remove(lokasi_file+nama_file)
        else:
            return False
    if DB_konfigurasi["kecepatan_pengejaan_tts"] == "tinggi":
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
    global DB_konfigurasi
    global Run, Music, Musik_dimainkan
    print_log("Modul musik dijalankan")
    while Run:
        if Musik_dimainkan != "" and Music:
            playlist = get_playlist(Musik_dimainkan)
            for musik in playlist:
                if not Music:
                    break
                # media = vlc.Media(DB_konfigurasi['folder_musik']+musik)
                media_player = vlc.MediaPlayer(DB_konfigurasi['folder_musik']+musik)
                media_player.play()
                time.sleep(1)
                print_log("VLC Memainkan "+musik)
                while media_player.is_playing() & Music:
                    time.sleep(1)
                media_player.stop()
                time.sleep(0.5)
            Musik_dimainkan = ""
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
    global DB_konfigurasi, DB_playlist
    global Run, Bell_dimainkan, Musik_dimainkan, Music
    print_log("Modul player dijalankan")
    while Run:
        if(Bell_dimainkan != ""):
            nama_playlist = Bell_dimainkan
            if nama_playlist.startswith(PENANDA_PLAYLIST):
                Musik_dimainkan = nama_playlist
                Music = True
                # PLAYIST_DIMAINKAN = ""
            else:
                Music = False
                playing = get_playlist(Bell_dimainkan)
                for play in playing:
                    play = DB_konfigurasi["folder_musik"]+play
                    if DEBUG:
                        print_log("playing "+play)
                    try:
                        playsound(play)
                    except Exception as error:
                        print_log("Gagal memainkan "+play)
                        print(error)
        Bell_dimainkan = ""
        time.sleep(0.5)
    print_log("Modul player berhenti")

# untuk pengumuman menggunakan text to speech
def pengumuman():
    global Run, Pengumuman, Bell_dimainkan, DB_konfigurasi
    print_log("Modul pengumuman dijalankan")
    while Run:
        if Pengumuman != "":
                file_output = DB_konfigurasi["folder_musik"]+"TTS_output.mp3"
                if os.path.isfile(file_output):
                    os.remove(file_output)
                print_log("Mengumumkan "+Pengumuman)
                try:
                    if DB_konfigurasi["kecepatan_pengejaan_tts"] == "tinggi":
                        gtts_slow = False
                    else:
                        gtts_slow = True
                    res = gTTS(text=Pengumuman, lang='id', slow=gtts_slow)
                    res.save(file_output)
                    # tunggu jika masih ada yang dimainkan
                    if DB_konfigurasi["tunggu_playlist_selesai"] == "Ya" :
                        while Bell_dimainkan != "":
                            time.sleep(1)
                    try:
                        if DB_konfigurasi["nada_pemberitahuan"] != "":
                            playsound(DB_konfigurasi["folder_musik"]+DB_konfigurasi["nada_pemberitahuan"])
                        playsound(file_output)
                    except Exception as error:
                        print_log("Gagal memainkan audio")
                        print(error)
                except Exception as e:
                    print_log("Pengumuman gagal")
                    print(e)
                Pengumuman = ""
        time.sleep(1)
    print_log("Modul pengumuman berhenti")

# Jam
# konsep baru
# dalam pengecekan looping, akan dilakukan looping kedua,
# dimana looping kedua akan melakukan looping selama setatus Alarm True, sedangkan looping utama akan sesuai dengan status program
# status alarm akan dirubah sesuai dengan hari yang akan dicek oleh looping utama dan dicek oleh looping alarm
# dalam pengecekan di looping alarm, akadn dicek apakah hari ini masih sama dengan hari yang dijalankan
# dalam pengecekkan looping utama akan dicek apakah hari ini libur atau tidak 
def alarm():
    global jam_sekarang, Run, Bell_dimainkan, Hari_masuk, Alarm, Now
    if DEBUG:
        print(Now.strftime("%d/%m/%Y"))
    # load_time()
    # if DEBUG:
    #     print("jam alarm : ", waktu_alarm)
    #     # print(waktu_alarm)
    print_log("Modul timer dijalankan")
    while Run:
        Alarm = False
        hari_ini = date_id()
        Now = datetime.datetime.now()
        tanggal = Now.strftime("%d/%m/%Y")
        
        #pengecekkan hari libur
        for hari in Hari_masuk:
            if hari == hari_ini:
                #pengecekkan tanggal libur
                for tgl in DB_libur:
                    # print(tgl)
                    Alarm = True
                    if tgl == tanggal:
                        Alarm = False
                # time.sleep(100)
        #perulangan yang baru
        if Alarm:
            while Alarm & Run:
                jam_alarm = load_time(DB_jadwal[hari_ini])
                jam_sekarang = time.strftime('%H:%M')
                for alarm in jam_alarm:
                    if jam_sekarang == alarm:
                        Bell_dimainkan = DB_jadwal[hari_ini][jam_sekarang]
                        print_log("Memainkan playlist "+Bell_dimainkan)
                        time.sleep(59)
                #cek apakah sudah berganti hari
                time.sleep(1)
                if(hari_ini != date_id()):
                    Alarm=False
                    print_log("Perhantian hari jadwal direset!")
        else:
            time.sleep(60)
    print_log("Modul alarm berhenti")

# interface untuk debug
def interface():
    global thread_alarm, Run, Bell_dimainkan, jam_sekarang, Alarm, Pengumuman
    print("\n")
    while Run:
        perintah = input("Perintah: ")
        if(perintah== "reload"):
            # print("perintah 1")
            load_config()
            Alarm=False
            # load_time()
        elif(perintah=="info"):
            # print("Jadwal : ")
            # print(DB_jadwal[date_id()])
            print("Jam server           : ",time.strftime('%H:%M'))
            print("Hari                 : ",date_id())
            print("Playlist saat ini    : ",Bell_dimainkan)
            print("status thread alarm  : ",thread_alarm.is_alive())
            print("status thread player : ",thread_player.is_alive())
            print("Alarm berjalan       : ",Alarm)
        elif(perintah=="pengumuman"):
            Pengumuman=input("Pengumuman : ")
        elif(perintah=="play"):
            Bell_dimainkan="bell"
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
    global Pengumuman, DB_jadwal, DB_playlist
    POST = '{}'
    if request.method == 'POST':
        POST = json.dumps(request.form)
        # print(request.form)
        if "isi" in request.form:
            Pengumuman = request.form.get('isi')
        elif "jadwal" in request.form:
            jadwal = request.form.get('jadwal')
            file_conf = json.load(open(FILE_KONFIGURASI))
            file_conf['jadwal'] = json.loads(jadwal)
            DB_jadwal = json.loads(jadwal)
            # print(json.dumps(file_conf, indent=4))
            with open(FILE_KONFIGURASI, 'w') as outfile:
                json.dump(file_conf, outfile, indent=4)
            load_config()
        elif "playlist" in request.form:
            playlist = request.form.get('playlist')
            file_conf = json.load(open(FILE_KONFIGURASI))
            file_conf['playlist'] = json.loads(playlist)
            DB_playlist = json.loads(playlist)
            # print(json.dumps(file_conf, indent=4))
            with open(FILE_KONFIGURASI, 'w') as outfile:
                json.dump(file_conf, outfile, indent=4)
            load_config()

    data = {"JADWAL":DB_jadwal, "PLAYLIST":DB_playlist, "TANGGAL_LIBUR":DB_libur, "KONFIGURASI":DB_konfigurasi,"POST":json.loads(POST)}
    return render_template('index.html', data=data)

@http.route("/api/<string:page>/<string:key>", methods=['GET', 'POST'])
def api(page="",key=""):
    global DB_jadwal, DB_konfigurasi, DB_playlist, DB_libur
    global http, Run, Alarm, Pengumuman, Now, Hari_masuk,jam_sekarang, Bell_dimainkan, Music

    err = {}
    response = ""
    if DB_konfigurasi['key_api']!= key:
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
                Pengumuman = data
                response = Pengumuman+" akan diumumkan"

    elif page == "info":
        informasi={}
        informasi['jam']=time.strftime('%H:%M')
        informasi['hari']=date_id()
        informasi['playlist_dimainkan']=Bell_dimainkan
        informasi['thread_alarm']=thread_alarm.is_alive()
        informasi['thread_player']=thread_player.is_alive()
        informasi['thread_pengumuman']=thread_pengumuman.is_alive()
        informasi['status_timer']=Alarm
        response = jsonify(informasi)

    elif(page== "reload"):
        load_config()
        Alarm = False
        Music = False
        response = ""
    elif page == "play":
        if post:
            playlist = request.form.get('playlist')
            if playlist in DB_playlist:
                Bell_dimainkan = playlist
                response = ""
            else:
                err['err'] = True
                err['pesan'] = "playlist tidak ditemukan"
                response = jsonify(err)
        elif DEBUG:
            Bell_dimainkan = "bell"
    elif page == "text2mp3":
        if post:
            text = request.form.get('text')
            nama_file = request.form.get('nama_file')
            if text != "" and nama_file != "":
                tts_to_mp3(text, nama_file)
        else:
            return render_template("text2mp3.html")

    else:
        err["err"] = True
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
    thread_music_player = threading.Thread(target=music_player, daemon=True)
    thread_alarm.start()
    thread_player.start()
    thread_pengumuman.start()
    thread_music_player.start()
    #radio client
    # if DB_konfigurasi["url_stream"] != "":
    #     icecast_client.init(DB_konfigurasi["url_stream"])
    # if DEVELOP:
    #     interface()
    # else:
    http.run(debug=DEBUG,host=DB_konfigurasi['listen'],port=DB_konfigurasi['port'])
        # while Run:
        #     time.sleep(1)