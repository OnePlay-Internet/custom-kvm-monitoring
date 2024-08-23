import os
import subprocess
from threading import Thread
import inotify.adapters

import ujson

from connection import create_influxdb_point, write_api, INFLUX_BUCKET, INFLUX_ORG


def get_vms_with_state():
    try:
        output_lines = subprocess.check_output(['virsh', 'list', '--all']).decode('utf-8').strip().split('\n')
        vm_stats = []
        keys = output_lines[0].split('   ')
        keys = [key.lower().strip() for key in keys]
        for line in output_lines[2:]:
            values = line.split('   ')
            vm_stat = dict()
            vm_stat[keys[0]] = values[0].strip()
            vm_stat[keys[1]] = values[1].strip()
            vm_stat[keys[2]] = values[2].strip()
            vm_stats.append(vm_stat)
        return vm_stats
    except Exception as e:
        return []


def get_kvm_stats():
    try:
        output = subprocess.check_output(
            ['sudo', '-S', 'kvmtop', '--cpu', '--mem', '--disk', '--net', '--io', '--host', '--verbose',
             '--printer=json', '--runs=1'], input=f'{os.getenv("ROOT_PASS")}\n', text=True)
        if output and output.startswith('{ "'):
            data = ujson.loads(output)
            return data
    except Exception as e:
        print(str(e))
    return {}


def sync_data_to_influx_db(data):
    try:
        point = create_influxdb_point('kvm_stats', data)
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        print(f"writing record for kvm_stats finished.")
    except Exception as e:
        return


def group_data_points(key_prefix, source_data):
    return {key: source_data[key] for key in source_data if key.startswith(key_prefix)}


def filter_and_group_host_stats(hostname, host_uuid, data):
    try:
        to_return = {}
        host_key_groups = {"cpu_": "cpustat", "ram_": "memory", "disk_": "disk", "net_": "nics", "psi_": "psistat"}
        for key in host_key_groups:
            data_group = group_data_points(key_prefix=key, source_data=data)
            if data_group:
                data_group.update({"host": hostname, "host_uuid": host_uuid})
                to_return[host_key_groups[key]] = data_group
        return to_return
    except Exception as e:
        print(e)
        return {}


def filter_and_group_vm_stats(hostname, host_uuid, data):
    try:
        to_return = {}
        vm_name = data.get('name', "")
        vm_id = data.get('UUID', "")
        host_key_groups = {"cpu_": "cpustat", "ram_": "memory", "disk_": "disk", "net_": "nics", "io_": "iostat", }
        for key in host_key_groups.keys():
            data_group = group_data_points(key_prefix=key, source_data=data)
            if key == 'cpu_':
                data_group.update({'state': data.get('state')})
            if data_group:
                data_group.update({"host": hostname, "host_uuid": host_uuid, "vm_name": vm_name, "vm_id": vm_id})
                to_return[f"vm_{host_key_groups[key]}"] = data_group
        return to_return
    except Exception as e:
        print(e)
        return {}


def send_data_to_influxdb(data):
    for key, value in data.items():
        if value:
            point = create_influxdb_point(key, value)
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
            print(f"writing record for {key} finished.")
    else:
        print('No data found')


def send_data(log):
    try:
        vms_list = get_vms_with_state()
        domains = log.get('domains', [])
        if not domains:
            for vm in vms_list:
                vm_stat = dict()
                vm_stat['name'] = vm.get('name')
                vm_stat['state'] = vm.get('state')
                domains.append(vm_stat)
        else:
            for domain in domains:
                domain.update({'state': 'running'})
        hostname = log.get("host", {}).get("host_name")
        host_uuid = log.get("host", {}).get("host_uuid")
        host_data = filter_and_group_host_stats(hostname, host_uuid, data=log.get('host'))
        send_data_to_influxdb(host_data)
        for vm_stats in domains:
            if vm_stats.get('state') == 'running':
                send_data_to_influxdb(filter_and_group_vm_stats(hostname, host_uuid, data=vm_stats))
        return True
    except Exception as e:
        print(str(e))
        return


def collect_data_continuously():
    log_file = "/home/vignesh/dev/kvmtop.logs"
    i = inotify.adapters.Inotify()
    i.add_watch(log_file)

    try:
        for event in i.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event

            if "IN_MODIFY" in type_names:
                with open(log_file, 'r') as file:
                    lines = file.readlines()
                    last_line = lines[-1].strip()
                    t1 = Thread(target=send_data, args=(last_line,))
                    t1.run()

    finally:
        i.remove_watch(log_file)


def collect_data():
    try:
        data = get_kvm_stats()
        return send_data(data)
    except Exception as e:
        print(e)
    return False


if __name__ == "__main__":
    collect_data()
