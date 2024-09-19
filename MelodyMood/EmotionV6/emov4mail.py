#8/04/2024
import streamlit as st
import numpy as np
from keras.models import load_model
import pandas as pd
from streamlit_webrtc import webrtc_streamer
import av
import cv2
import mediapipe as mp
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import csv
import ssl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random

CLIENT_ID = "7fb2bbe65a8145a6995b2ff519c63492"
CLIENT_SECRET = "61305c3b09fa42579be968dfdd8308da"

client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)



# Kullanıcı verilerini tutacak CSV dosyasının yolu
USER_DATA_CSV_PATH = "user_data.csv"
MUSIC_LIST_PATH ="music_list.csv"
MODEL_PATH = "model.h5"
MODEL_EMO_PATH = " emotion.npy"
MODEL_LABEL_PATH = "labels.npy"
VERIFICATION_CODES_CSV_PATH = "verification_codes.csv"

def reverse_emotion(emotion):
    if emotion == "happy":
        emotion = "sad"
        return emotion
    elif emotion == "sad":
        emotion = "happy"
        return emotion
    elif emotion == "rocrock":
        emotion = "susurprise"
        return emotion
    elif emotion == "neatural":
        emotion = "angry"
        return emotion
    elif emotion == "susurprise":
        emotion = "rocrock"
        return emotion
    else:
        emotion = "neatural"
        return emotion

def get_spotify_uri(track_name):
    # Şarkıyı ara ve ilk eşleşen sonucun URI'sini al
    results = sp.search(q=track_name, limit=1)
    if results and results['tracks'] and results['tracks']['items']:
        track_uri = results['tracks']['items'][0]['uri']
        return track_uri
    else:
        return None

def get_playlist_tracks(playlist_id):
    # Playlistteki tüm parçaları al
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    
    # Tüm sayfaları al
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    
    # Parça adlarını bir liste olarak döndür
    return [track['track']['name'] for track in tracks]

def get_user_info(username):
    user_data = load_user_data()
    user_info = user_data[user_data["username"] == username]
    return user_info

def profile_page():
    st.title("Profile")

    # Check if user is logged in
    if "username" not in st.session_state:
        st.error("You are not logged in.")
        return

    # Get logged-in user's information
    username = st.session_state["username"]
    user_info = get_user_info(username)

    if not user_info.empty:
        st.write(f"**Username:** {user_info['username'].values[0]}")
        st.write(f"**Age:** {user_info['age'].values[0]}")
        st.write(f"**Gender:** {user_info['gender'].values[0]}")
        st.write(f"**Country:** {user_info['country'].values[0]}")
        st.write(f"**Email:** {user_info['email'].values[0]}")

        # Log out button
        if st.button("Oturumu Kapat", key = "logout_button"):
            st.session_state["login_state"] = False
            st.session_state["username"] = ""
            st.success("Oturum başarı ile sonlandırıldı")
    else:
        st.error("User information not found.")


def generate_verification_code():
    return str(random.randint(100000, 999999))

def save_verification_code(email, verification_code):
    csv_file = "verification_codes.csv"

    # Write the verification code to the CSV file
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([email, verification_code])

def email_exists(email):
    csv_file = "user_data.csv"

    # Check if the email exists in the CSV file
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[5] == email:  
                return True
    return False



def send_verification_code(receiver_email, verification_code):
    sender_email = "melody_mood@hotmail.com" 
    sender_password = "MelodyMood123456"  

    subject = "Email Verification Code"
    body = f"Your verification code is: {verification_code}"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain", "utf-8"))

    server = smtplib.SMTP("smtp-mail.outlook.com",587)
    server.starttls()
    server.ehlo()
    server.login(sender_email,sender_password)
    server.sendmail(sender_email, receiver_email, message.as_string())
    server.quit()


def verify_verification_code(email, verification_code):
    try:
        with open(VERIFICATION_CODES_CSV_PATH, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == email and row[1] == verification_code:
                    return True
        return False
    except FileNotFoundError:
        return False

# Function to update password in user data
def update_password(email, new_password):
    try:
        user_data = pd.read_csv(USER_DATA_CSV_PATH)
        user_data.loc[user_data["email"] == email, "password"] = new_password
        user_data.to_csv(USER_DATA_CSV_PATH, index=False)
        return True
    except FileNotFoundError:
        return False


    
def forgot_password():
    st.title("Forgot Password")
    email = st.text_input("Email")

    if st.button("Reset Password"):
        # Check if email exists in the database
        if email_exists(email):
            # Generate and save verification code
            verification_code = generate_verification_code()
            save_verification_code(email, verification_code)

            # Send verification code to the user's email (optional)
            send_verification_code(email, verification_code)

            st.success("A six-digit verification code has been sent to your email.")
        else:
            st.error("Email not found. Please enter a valid email address.")


def change_password():
    st.title("Change Password")
    email = st.text_input("Email", key="change_password_email")
    verification_code = st.text_input("Verification Code")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")

    if st.button("Change Password"):
        if not email_exists(email):
            st.error("Email not found. Please enter a valid email address.")
            return

        if not verify_verification_code(email, verification_code):
            st.error("Invalid verification code. Please enter the correct code.")
            return

        if new_password != confirm_password:
            st.error("Passwords do not match. Please make sure the passwords match.")
            return

        if update_password(email, new_password):
            st.success("Password successfully changed. You can now log in with your new password.")
        else:
            st.error("Failed to change password. Please try again later.")


# Kullanıcı verilerini yükleyen ve kaydeden fonksiyonlar
def load_user_data():
    try:
        user_data = pd.read_csv(USER_DATA_CSV_PATH)
        return user_data
    except FileNotFoundError:
        # Eğer dosya bulunamazsa, boş bir DataFrame döndür
        return pd.DataFrame(columns=["username", "password","age","gender","country"])


def save_user_data(user_data):
    user_data.to_csv(USER_DATA_CSV_PATH, index=False)

# Yeni kullanıcıyı kaydetme ve doğrulama fonksiyonu
def validate_registration(username, password, age, gender, country, email):
    user_data = load_user_data()
    if username in user_data["username"].values:
        st.error("Bu kullanıcı adı zaten kullanılıyor! Lütfen farklı bir kullanıcı adı seçin.")
        return False
    else:
        # New user registration including additional fields
        new_user = {"username": username, "password": password, "age": age, "gender": gender, "country": country, "email": email}
        user_data = pd.concat([user_data, pd.DataFrame([new_user])], ignore_index=True)
        save_user_data(user_data)  # Save user data
        st.success("Başarıyla kayıt oldunuz! Lütfen giriş yapın.")
        return True



# Kayıt ekranı
def register():
    st.title("Kayıt Ol")
    new_username = st.text_input("Yeni Kullanıcı Adı", key="new_username")
    new_password = st.text_input("Yeni Şifre", type="password", key="new_password")
    confirm_password = st.text_input("Şifreyi Onayla", type="password", key="confirm_password")
    
    # New fields for additional personal information
    age = st.number_input("Yaş", min_value=1, max_value=150, step=1, key="age")
    gender = st.radio("Cinsiyet", options=["Erkek", "Kadın", "Diğer"], key="gender")
    country = st.text_input("Ülke", key="country")
    email = st.text_input("Mail adresi", key="email")
    
    
    if st.button("Kayıt Ol"):
        if new_password == confirm_password:
            # Validate registration including additional fields
            if email.strip() == "" or new_password.strip() == "" or new_username.strip() == "" or country.strip() == "":
                st.error("Kutucuklar boş olamaz!")
            else:
                success = validate_registration(new_username, new_password, age, gender, country, email)
                if success:
                    # Clear input fields after successful registration
                    new_username = ""
                    new_password = ""
                    confirm_password = ""
                    age = None
                    gender = ""
                    country = ""
                    email = ""
                    

        else:
            st.error("Şifreler eşleşmiyor! Lütfen tekrar deneyin.")

# Kullanıcı girişini doğrulama fonksiyonu
def validate_login(username, password):
    user_data = load_user_data()
    user_index = user_data[user_data["username"] == username].index
    if user_index.empty:
        st.error("Kullanıcı adı veya şifre hatalı!")
        return False
    else:
        actual_password = user_data.loc[user_index[0], "password"]
        if password == actual_password:
            return True
        else:
            st.error("Kullanıcı adı veya şifre hatalı!")
            return False

# Kullanıcı girişi ekranı
def login():
    username = st.text_input("Kullanıcı Adı", key="login_username")
    password = st.text_input("Şifre", type="password", key="login_password")
    return username, password

# Ana uygulama
def main():
    # Duygu verisini yükle, yoksa boş bir dize olarak ayarla
    try:
        emotion = np.load("emotion.npy")[0]
    except FileNotFoundError:
        emotion = ""

    # Kullanıcı girişi kontrolü ve session_state'in başlatılması
    if "login_state" not in st.session_state:
        st.session_state["login_state"] = False
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "login"

    st.sidebar.title("🏠")

    # Kayıt ve giriş sayfaları arasında geçiş yapmak için st.page_link kullanılıyor
    if st.sidebar.button("Kayıt Ol", key="register_page"):
        st.session_state["current_page"] = "register"
    if st.sidebar.button("Giriş", key="login_page"):
        st.session_state["current_page"] = "login"

    if st.session_state["current_page"] == "register":
        register()
    elif st.session_state["current_page"] == "login":
        username, password = login()
        if st.button("Giriş"):
            if validate_login(username, password):
                st.success("Başarıyla giriş yaptınız!")
                st.session_state["login_state"] = True
                st.session_state["username"] = username  # Kullanıcı adını sakla


    if st.sidebar.button("Şifremi Unuttum"):
        st.session_state["current_page"] = "forgot_password"

    if st.session_state["current_page"] == "forgot_password":
        forgot_password()

    if st.sidebar.button("Şifremi Degistir"):
        st.session_state["current_page"] = "change_password"

    if st.session_state["current_page"] == "change_password":
        change_password()

    if st.sidebar.button("Profile"):
        st.session_state["current_page"] = "profile"
    
    if st.session_state["current_page"] == "profile":
        profile_page()



    # Kullanıcı girişi başarılıysa veya oturum açma durumu varsa devam edin
    if st.session_state["login_state"]:
        # Sağ üst köşede kullanıcı adını göster
        st.sidebar.write(f"Kullanıcı: {st.session_state['username']}")

        # Oturumu kapatma düğmesi
        if st.sidebar.button("Oturumu Kapat"):
            st.session_state["login_state"] = False
            st.session_state["username"] = ""
        # Kullanıcı doğrulandığında duygu analizi ve müzik önerme sayfasına yönlendir
        st.header("MelodyMood")
        
        # Eğitilmiş modeli yükle
        model = load_model("model.h5")
        # Etiketleri yükle
        label = np.load("labels.npy")
        # Mediapipe'nin holistic ve hands modüllerini kullanmak için tanımlamaları yap
        holistic = mp.solutions.holistic
        hands = mp.solutions.hands
        holis = holistic.Holistic()
        drawing = mp.solutions.drawing_utils

        # Video akışını işleyen sınıf
        class EmotionProcessor:
            def recv(self, frame):
                # Gelen görüntüyü OpenCV formatına dönüştür
                frm = frame.to_ndarray(format="bgr24")

                # Görüntüyü yatay olarak çevir
                frm = cv2.flip(frm, 1)

                # Mediapipe ile yüz ve el izleme işlemlerini gerçekleştir
                res = holis.process(cv2.cvtColor(frm, cv2.COLOR_BGR2RGB))

                lst = []

                # Yüz izleme sonucu varsa
                if res.face_landmarks:
                    # Yüz izleme noktalarını diziye ekle
                    for i in res.face_landmarks.landmark:
                        lst.append(i.x - res.face_landmarks.landmark[1].x)
                        lst.append(i.y - res.face_landmarks.landmark[1].y)

                    # Sol el izleme sonucu varsa
                    if res.left_hand_landmarks:
                        for i in res.left_hand_landmarks.landmark:
                            lst.append(i.x - res.left_hand_landmarks.landmark[8].x)
                            lst.append(i.y - res.left_hand_landmarks.landmark[8].y)
                    else:
                        for i in range(42):
                            lst.append(0.0)

                    # Sağ el izleme sonucu varsa
                    if res.right_hand_landmarks:
                        for i in res.right_hand_landmarks.landmark:
                            lst.append(i.x - res.right_hand_landmarks.landmark[8].x)
                            lst.append(i.y - res.right_hand_landmarks.landmark[8].y)
                    else:
                        for i in range(42):
                            lst.append(0.0)

                    # Özellik vektörünü yeniden şekillendir
                    lst = np.array(lst).reshape(1, -1)

                    # Modeli kullanarak tahmin yap
                    pred = label[np.argmax(model.predict(lst))]


                    cv2.putText(frm, pred, (50, 50), cv2.FONT_ITALIC, 1, (255, 0, 0), 2)

                    # Duygu verisini kaydet
                    np.save("emotion.npy", np.array([pred]))

                # Yüz ve el izleme sonuçlarını görüntüye çiz
                drawing.draw_landmarks(frm, res.face_landmarks, holistic.FACEMESH_TESSELATION,
                                       landmark_drawing_spec=drawing.DrawingSpec(color=(0, 0, 255), thickness=-1,
                                                                                  circle_radius=1),
                                       connection_drawing_spec=drawing.DrawingSpec(thickness=1))
                drawing.draw_landmarks(frm, res.left_hand_landmarks, hands.HAND_CONNECTIONS)
                drawing.draw_landmarks(frm, res.right_hand_landmarks, hands.HAND_CONNECTIONS)

                # Çıktıyı VideoFrame formatına dönüştür
                return av.VideoFrame.from_ndarray(frm, format="bgr24")

        # WebRTC akışını başlat
        webrtc_streamer(key="key", desired_playing_state=True,
                        video_processor_factory=EmotionProcessor)

        # "Recommend me songs" butonuna tıklandığında
        btn = st.button("Şarkı Öner!")
        btn2 = st.button("Modumu Değiştir!")

    
        
        
        playlist_mapping = {
        "happy": "32c21ycnuAUbTCUXLnNFdx",
        "sad": "1n9fj1QQNSzCTMzFLlm28n",
        "rocrock": "37i9dQZF1DX1tyCD9QhIWF",
        "neutral":"37i9dQZF1DX4OzrY981I1W",
        "susurprise":"6LYSq9TKmka9P0zupclIcu",
        "angry":"37i9dQZF1DWSVO64ma1pNY"
    
}
        
        # "Şarkı Öner!" butonuna tıklanınca
        if btn:
            # Duygu verisi yoksa uyarı göster
            if not(emotion):
                st.warning("Duygunuzu Yakalayamadım!")
            else:    
                playlist_id = playlist_mapping.get(emotion)
                music_list = get_playlist_tracks(playlist_id)
                st.write(f"**{emotion.capitalize()}** duygusu için önerilen 5 rastgele müzik:")
                
                # Select 5 random songs from the playlist
                random_songs = random.sample(music_list, 5)
                
                for music in random_songs:
                    # Şarkı adından Spotify URI'sini al
                    track_uri = get_spotify_uri(music)
                    if track_uri:
                        # Spotify URI'sini çalma bağlantısına dönüştür ve göster
                        spotify_play_url = f"spotify:track:{track_uri.split(':')[2]}"
                        st.write("- [" + music + f"](spotify:track:{spotify_play_url})")
                        # Duygu verisini sıfırla
                        np.save("emotion.npy", np.array([""]))
                        
        elif btn2:
            # Duygu verisi yoksa uyarı göster
            if not(emotion):
                st.warning("Duygunuzu Yakalayamadım!")
            else:
                emotion = reverse_emotion(emotion)
                playlist_id = playlist_mapping.get(emotion)
                music_list = get_playlist_tracks(playlist_id)
                st.write(f"**{emotion.capitalize()}** duygusu için önerilen 5 rastgele müzik:")
                
                # Select 5 random songs from the playlist
                random_songs = random.sample(music_list, 5)
                
                for music in random_songs:
                    # Şarkı adından Spotify URI'sini al
                    track_uri = get_spotify_uri(music)
                    if track_uri:
                        # Spotify URI'sini çalma bağlantısına dönüştür ve göster
                        spotify_play_url = f"spotify:track:{track_uri.split(':')[2]}"
                        st.write("- [" + music + f"](spotify:track:{spotify_play_url})")
                        # Duygu verisini sıfırla
                        np.save("emotion.npy", np.array([""]))

    else:
        st.info("Lütfen giriş yapın.")

if __name__ == "__main__":
    main()
