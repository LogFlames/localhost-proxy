import os
import subprocess

def create_nginx_conf(domain, port):
    nginx_conf_dir = "/etc/nginx/sites-enabled"
    conf_file_path = os.path.join(nginx_conf_dir, f"{domain}.conf")

    conf_content = f"""
    server {{
        listen 80;
        server_name {domain};

        location / {{
            proxy_pass http://localhost:{port};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }}
    }}
    """

    try:
        with open(conf_file_path, "w") as conf_file:
            conf_file.write(conf_content)

        print(f"NGINX configuration written to {conf_file_path}")

        subprocess.run(["nginx", "-t"], check=True)

        subprocess.run(["service", "nginx", "reload"], check=True)
        print("NGINX reloaded successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error occurred while testing or reloading NGINX: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def disable_nginx_proxy(domain):
    nginx_conf_dir = "/etc/nginx/sites-enabled"
    conf_file_path = os.path.join(nginx_conf_dir, f"{domain}.conf")

    try:
        os.remove(conf_file_path)

        print(f"NGINX configuration removed from {conf_file_path}")

        subprocess.run(["service", "nginx", "reload"], check=True)
        print("NGINX reloaded successfully.")

    except FileNotFoundError:
        print(f"NGINX configuration file not found: {conf_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while reloading NGINX: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
