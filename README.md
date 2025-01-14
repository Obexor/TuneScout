# 🎵 Streamlit Music Upload, Streaming, and Equalizer App

A simple yet powerful web application built with **Streamlit** that allows users to upload music, store its metadata and audio fingerprints in **Amazon DynamoDB**, and stream songs securely using pre-signed URLs from **Amazon S3**. Additionally, it includes an equalizer feature for enhancing the audio playback experience.

This project demonstrates the integration of cloud services with a user-friendly interface for music upload, metadata management, deduplication using fingerprints, secure streaming, and audio equalization.

---

## 🚀 Features

1. **Song Upload**:
   - Upload MP3/WAV audio files.
   - Automatically generate audio fingerprints for deduplication.
   - Input metadata (artist, title, and album) or use defaults.

2. **Duplicate Detection**:
   - Prevent duplicate entries by checking stored fingerprints in DynamoDB.

3. **Stream Songs**:
   - List all uploaded songs.
   - Securely stream songs from AWS S3 using pre-signed URLs.

4. **Audio Equalizer**:
   - Adjust audio frequencies to enhance playback.
   - Save and apply custom equalizer settings.

5. **AWS Integration**:
   - **DynamoDB**: Store song metadata and fingerprints.
   - **S3**: Store audio files and generate pre-signed URLs for secure access.

---

## 🛠️ Technologies Used

- **Frontend**:
  - [Streamlit](https://streamlit.io/) - A fast and simple way to create data-driven web applications in Python.

- **Cloud Services**:
  - **Amazon S3**: For storing audio files with secure, scalable object storage.
  - **Amazon DynamoDB**: For storing song metadata and audio fingerprints.

- **Backend**:
  - **Python (3.12.3)**: With the following libraries:
    - [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html): AWS SDK for Python.
    - [pandas](https://pandas.pydata.org/): For any data manipulation.
    - [numpy](https://numpy.org/): To support fingerprint generation.
    - [Jinja2](https://palletsprojects.com/p/jinja/): For rendering templates if needed.
    - [pydub](https://pydub.com/): For audio processing and equalization.

---

## 📦 Installation

### Prerequisites
- Python 3.12+
- **AWS Account** with the IAM user having access to:
  - S3 Bucket for storing songs (`s3:GetObject`, `s3:PutObject` permissions).
  - DynamoDB Table for storing songs metadata (`dynamodb:PutItem`, `dynamodb:Scan` permissions).

### Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/streamlit-music-app.git
   cd streamlit-music-app
   ```

2. **Install Dependencies**:
   Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure AWS Credentials**:
   Provide your AWS credentials (`aws_access_key_id` and `aws_secret_access_key`) either using:
   - **Environment variables**:
     ```bash
     export AWS_ACCESS_KEY_ID='your-access-key'
     export AWS_SECRET_ACCESS_KEY='your-secret-key'
     export AWS_REGION='your-region'
     export AWS_S3_BUCKET_NAME='your-bucket-name'
     export DYNAMODB_TABLE_NAME='your-dynamodb-table-name'
     ```
   - OR using AWS CLI configuration:
     ```bash
     aws configure
     ```

4. **Set Up Environment Variables**
   Create a `.env` file with the following structure:
   ```
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_REGION=your-region
   AWS_S3_BUCKET_NAME=your-bucket-name
   DYNAMODB_TABLE_NAME=your-dynamodb-table-name
   ```

5. **Run the Application**:
   Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```

6. Open your browser at **http://localhost:8501** to view the app.

---

## 🛡️ AWS Setup

### 1. **Create an S3 Bucket**
   - Go to the AWS Management Console, open **S3**, and create a bucket.
   - Note the bucket name as it will be required in your app environment.

### 2. **Set Up a DynamoDB Table**
   - Open the DynamoDB service in AWS Console and create a new table.
   - Define a primary key as `song_id` (Number) or any field you'd like to use.

### 3. **IAM User Permissions**
   Ensure your IAM user/role has permissions for:
   - `s3:PutObject`
   - `s3:GetObject`
   - `dynamodb:PutItem`
   - `dynamodb:Scan`

---

## ⚙️ Project Structure


---

## 🔑 Key Functionalities

### 1. **Uploading Songs**
   - Upload a song (MP3/WAV).
   - Input metadata like title, artist, and album.
   - Automatically generates fingerprints to detect duplicates.

### 2. **Database Operations**
   - Add new songs to DynamoDB with a unique identifier (`song_id`).
   - Ensure no duplicate uploads by checking existing fingerprints.

### 3. **Secure Streaming**
   - List uploaded songs and their metadata from DynamoDB.
   - Use pre-signed URLs to securely stream files directly from S3 in the browser.

### 4. **Audio Equalizer**
   - Adjust audio frequencies (bass, mid, treble) to enhance playback.
   - Save custom equalizer settings for future use.

---

## ❓ FAQs

### 1. **How are duplicates identified?**
   Duplicates are identified by generating **audio fingerprints** for each song and comparing them to records in DynamoDB. If a match exists, the song is not uploaded again.

### 2. **What is a pre-signed URL?**
   Pre-signed URLs allow temporary, secure access to S3 files without exposing your bucket publicly. The app uses boto3 to generate these URLs.

### 3. **What happens if metadata is missing?**
   The app uses default values (e.g., "Unknown Title", "Unknown Artist") if metadata is not provided.

### 4. **How does the equalizer work?**
   The equalizer allows users to adjust audio frequencies to enhance playback. Users can save their custom settings and apply them to any song.

---

## 🤝 Contributions

Contributions are welcomed! Fork the repository, create a branch, and start a pull request with your changes.

---

## 📝 License


---

## 📧 Contact

If you have any questions or need support, feel free to reach out to:

👤 **Tobias Obwexer**  
📧 [Ot8569@mci4me.at](mailto:Ot8569@mci4me.at)

👤 **Lennard Pöll**  
📧 [pl5525@mci4me.at](mailto:pl5525@mci4me.at)
