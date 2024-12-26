import math
import geocoder
from flask import Flask, render_template, request
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://kapiarso:kapiarso@mahasiswa.v2wsc.mongodb.net/?retryWrites=true&w=majority&appName=Mahasiswa"
client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("Your program is ready to use!!")
except Exception as e:
    print(f"Error")
    exit()

db = client["mahasiswa"]
collection = db["ipaddress"]

app = Flask(__name__)

class Lokasi:
    def __init__(self, lintang, bujur, ip_address, region, city, isp):
        self.lintang = lintang
        self.bujur = bujur
        self.ip_address = ip_address
        self.region = region
        self.city = city
        self.isp = isp

class Qiblat:
    kaabah_lat = 21.4225
    kaabah_lon = 39.8262

    @staticmethod
    def convert_to_radians(degrees):
        return math.radians(degrees)

    @staticmethod
    def hitung_arah_qiblat(lokasi: Lokasi):
        kaabah_lat_rad = Qiblat.convert_to_radians(Qiblat.kaabah_lat)
        kaabah_lon_rad = Qiblat.convert_to_radians(Qiblat.kaabah_lon)
        user_lat_rad = Qiblat.convert_to_radians(lokasi.lintang)
        user_lon_rad = Qiblat.convert_to_radians(lokasi.bujur)

        delta_lon = kaabah_lon_rad - user_lon_rad

        x = math.sin(delta_lon) * math.cos(kaabah_lat_rad)
        y = math.cos(user_lat_rad) * math.sin(kaabah_lat_rad) - \
            math.sin(user_lat_rad) * math.cos(kaabah_lat_rad) * math.cos(delta_lon)

        qiblat_angle_rad = math.atan2(x, y)
        qiblat_angle_deg = math.degrees(qiblat_angle_rad)

        if qiblat_angle_deg < 0:
            qiblat_angle_deg += 360

        return qiblat_angle_deg

class Aplikasi:
    def __init__(self):
        self.lokasi_pengguna = None
        self.nama = None

    def dapatkan_lokasi_otomatis(self):
        lokasi = geocoder.ip('me')
        if lokasi.ok:
            ip_address = lokasi.ip
            region = lokasi.region
            city = lokasi.city
            isp = lokasi.provider
            self.lokasi_pengguna = Lokasi(
                lokasi.latlng[0], 
                lokasi.latlng[1], 
                ip_address, 
                region, 
                city,
                isp
            )
        else:
            raise Exception("Gagal mendeteksi lokasi")

    def simpan_ke_database(self, arah_qiblat):
        data = {
            "nama": self.nama,
            "lintang": self.lokasi_pengguna.lintang,
            "bujur": self.lokasi_pengguna.bujur,
            "ip_address": self.lokasi_pengguna.ip_address,
            "region": self.lokasi_pengguna.region,
            "city": self.lokasi_pengguna.city,
            "isp": self.lokasi_pengguna.isp,
            "arah_qiblat": arah_qiblat
        }
        collection.insert_one(data)

    def hitung_arah_qiblat(self):
        arah_qiblat = Qiblat.hitung_arah_qiblat(self.lokasi_pengguna)
        return arah_qiblat

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nama = request.form['nama']
        aplikasi = Aplikasi()
        aplikasi.nama = nama
        aplikasi.dapatkan_lokasi_otomatis()
        arah_qiblat = aplikasi.hitung_arah_qiblat()
        aplikasi.simpan_ke_database(arah_qiblat)

        return render_template('result.html', nama=nama, arah_qiblat=arah_qiblat)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
