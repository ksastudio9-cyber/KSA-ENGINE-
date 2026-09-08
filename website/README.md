# Independent KSA Engine Website

This folder is a self-contained static website. It does not call GitHub, GitHub Releases, or any external API. Put the Windows build at:

```text
website/downloads/KSA.exe
```

Then serve the folder from any independent host, VPS, object storage bucket, or local machine:

```bash
python website/server.py --host 0.0.0.0 --port 8080
```

The public download path is:

```text
/downloads/KSA.exe
```

For production, place a reverse proxy such as Nginx or Caddy in front of the server and configure HTTPS. The repository does not include the binary itself because generated executables are release artifacts; copy the built `KSA.exe` into `website/downloads/` when deploying the independent site.