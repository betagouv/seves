import paramiko
from testcontainers.sftp import SFTPContainer


def test_fetch_export_agricoll_contacts_command():
    with SFTPContainer() as sftp_container:
        host_ip = sftp_container.get_container_host_ip()
        host_port = sftp_container.get_exposed_sftp_port()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host_ip, host_port, "basic", "password")
