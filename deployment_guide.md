# Complete Oracle Cloud + Coolify Deployment Guide

This guide explains how to deploy your Video Downloader PWA WebApp using **Oracle Cloud Infrastructure (OCI)** for free hosting/bandwidth (10 TB) and **Coolify** for a Render-like deployment experience.

---

## Step 1: Push Your Code to GitHub

First, make sure your local code is uploaded to GitHub.

1. Open your terminal in `videoDownloaderProject` folder.
2. Run these commands:
   ```bash
   git init
   git add .
   git commit -m "feat: add PWA support and blob downloads with background cleanup"
   ```
3. Go to [GitHub](https://github.com), create a new **Private** or **Public** repository.
4. Copy the repository link and run:
   ```bash
   git branch -M main
   git remote add origin <YOUR_GITHUB_REPO_URL>
   git push -u origin main
   ```

---

## Step 2: Sign Up for Oracle Cloud & Create a VM

1. Go to [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/) and sign up.
2. Go to **Compute Instances** -> **Create Instance**.
3. **Configure the Instance:**
   * **Name:** `streamglide-server`
   * **Image:** Select **Ubuntu** (standard configuration, e.g. Ubuntu 22.04 or 24.04).
   * **Shape:** Select **Always Free Eligible** (either VM.Standard.E2.1.Micro OR the ARM Ampere VM with up to 4 cores / 24 GB RAM if available).
   * **SSH Keys:** Under "Save SSH Keys", click **Save Private Key** (this downloads a `.key` file to your PC). **Do not lose this file.**
4. Click **Create** and wait 2 minutes. Copy your **Public IP Address** (e.g. `152.67.x.x`).

---

## Step 3: Open Security Ports in OCI Console

By default, OCI blocks incoming web traffic. Let's open port `80`, `443`, and `3000` (for Coolify dashboard).

1. On the Instance Details page, click on your **Virtual Cloud Network (VCN)** link.
2. Under "Resources", click **Security Lists**.
3. Click on the **Default Security List**.
4. Click **Add Ingress Rules** and add these three rules:
   * **Rule 1 (HTTP):** Source CIDR: `0.0.0.0/0`, IP Protocol: `TCP`, Destination Port Range: `80`
   * **Rule 2 (HTTPS):** Source CIDR: `0.0.0.0/0`, IP Protocol: `TCP`, Destination Port Range: `443`
   * **Rule 3 (Coolify Dashboard):** Source CIDR: `0.0.0.0/0`, IP Protocol: `TCP`, Destination Port Range: `3000`
5. Click **Add Ingress Rules**.

---

## Step 4: Login to your VM and Install Coolify

1. Open PowerShell or Command Prompt on your computer.
2. Navigate to the folder where you saved your `.key` file.
3. Change file permissions of the key (if you are on Linux/Mac, run `chmod 400 your-key.key`).
4. SSH into the VM:
   ```bash
   ssh -i your-key.key ubuntu@<YOUR_VM_PUBLIC_IP>
   ```
5. Once logged in, run this single command to install Coolify:
   ```bash
   curl -fsSL https://assets.coolify.io/install.sh | bash
   ```
6. The installation script will automatically install Docker and Coolify. It will take 2-4 minutes.
7. Once finished, it will output a success message showing your URL:
   `http://<YOUR_VM_PUBLIC_IP>:3000`

---

## Step 5: Configure Coolify Dashboard

1. Open your browser and go to `http://<YOUR_VM_PUBLIC_IP>:3000`.
2. Create your administrator account (email and password).
3. Connect your GitHub Account:
   * Go to **Keys & Sources** -> **GitHub App** -> Click **Create New GitHub App**.
   * Follow the steps to link your GitHub profile. This allows Coolify to access your repositories.

---

## Step 6: Deploy Your Webapp inside Coolify

1. On the Coolify home screen, click **Create New Project**.
2. Select **Application** -> **GitHub Repository**.
3. Select your `videoDownloaderProject` repository.
4. **Choose build pack:** Select **Nixpacks** or **Docker** (Nixpacks is recommended as it auto-detects Python).
5. **Configure Commands:**
   * Coolify will automatically recognize it's a Python/FastAPI app.
   * **Build Command:** `pip install -r requirements.txt` (or leave empty if auto-configured).
   * **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. **Expose Ports:** Set the Port to `8000` (FastAPI default). Coolify will automatically route external port `80`/`443` traffic to it.
7. Click **Deploy**. Within 2-3 minutes, your site will be live!

---

## Step 7: Connect Domain & Enable SSL (HTTPS)

1. Go to your Domain Registrar (GoDaddy, Hostinger, Namecheap, etc.) DNS Panel.
2. Add an **A Record**:
   * **Host:** `@` (for yourdomain.com) or `www`
   * **Points to:** `<YOUR_VM_PUBLIC_IP>`
3. In Coolify, open your deployed Application settings.
4. Under the **"Domains"** input box, write: `https://yourdomain.com`
5. Click **Save**. Coolify will automatically configure SSL Certificates via Let's Encrypt.
6. Open `https://yourdomain.com` on your mobile phone or browser. You will see the **Install App** button pop up!

---

# Requirements Checklist for Local Repo
Ensure these files are present in your root directory before pushing to GitHub:
- `main.py` (FastAPI backend)
- `index.html` (Frontend HTML)
- `style.css` (Frontend CSS)
- `app.js` (Frontend JS)
- `manifest.json` (PWA definition)
- `sw.js` (PWA Service Worker)
- `icon-192.png` & `icon-512.png` (App Icons)
- `requirements.txt` (List of dependencies)
