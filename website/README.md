# Independent KSA Engine Website

This folder is a self-contained static website. It does not call GitHub, GitHub Releases, or any external API. Put the Windows build at:

```text
website/downloads/KSA ENGINE.exe
```

Then serve the folder from any independent host, VPS, object storage bucket, or local machine. The engine itself is fully native C++; the website is static and does not require a Python runtime.

For a standalone native server, build the project with CMake and run:

```bash
./build/native/ksa_download_server --root website --port 8080
```

The download is then available at `/downloads/KSA%20ENGINE.exe`. Deploy the `website/` directory and `ksa_download_server` to your own VPS or Windows server to remove GitHub from the download path completely.

The public download path is:

```text
/downloads/KSA%20ENGINE.exe
```

For production, place a reverse proxy such as Nginx or Caddy in front of the server and configure HTTPS. The repository does not include the binary itself because generated executables are release artifacts; copy the built `KSA ENGINE.exe` into `website/downloads/` when deploying the independent site.