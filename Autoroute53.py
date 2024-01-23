import boto3
import csv
import argparse
from tqdm import tqdm

def read_domains(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

def export_to_csv(zone_id, zone_name, client):
    paginator = client.get_paginator('list_resource_record_sets')
    with open(f"{zone_name}.csv", 'w', newline='') as csvfile:
        fieldnames = ['Name', 'Type', 'TTL', 'Value']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for page in paginator.paginate(HostedZoneId=zone_id):
            for record in page['ResourceRecordSets']:
                values = [r['Value'] for r in record.get('ResourceRecords', [])]
                writer.writerow({'Name': record['Name'], 'Type': record['Type'], 'TTL': record.get('TTL', 'NA'), 'Value': ', '.join(values)})

def main(file_path=None, domain=None):
    client = boto3.client('route53')
    paginator = client.get_paginator('list_hosted_zones')
    domain_list = []
    if file_path:
        domain_list = read_domains(file_path)
    elif domain and domain != 'full':
        domain_list = [domain]
    total_zones = sum(1 for _ in paginator.paginate())
    with tqdm(total=total_zones, desc="Overall Progress", colour='yellow') as pbar:
        zone_pages = paginator.paginate()
        for page in zone_pages:
            for zone in tqdm(page['HostedZones'], desc="Exporting Zones", leave=False):
                zone_name = zone['Name'].rstrip('.')
                if domain == 'full' or zone_name in domain_list:
                    zone_id = zone['Id'].split('/')[-1]
                    export_to_csv(zone_id, zone_name, client)
            pbar.update(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export DNS Records from AWS Route53')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', help='Path to the file containing domain names')
    group.add_argument('-d', '--domain', help='Specific domain name or "full" for all domains')
    args = parser.parse_args()
    main(file_path=args.file, domain=args.domain)
