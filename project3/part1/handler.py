import json
import logging
import boto3
import os
import subprocess


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def video_splitting_cmdline(video_filename):
    filename = os.path.basename(video_filename)
    outfile = os.path.splitext(filename)[0] + ".jpg"

    split_cmd = 'ffmpeg -i ' + video_filename + ' -vframes 1 ' + '/tmp/' + outfile
    try:
        subprocess.check_call(split_cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)

    fps_cmd = 'ffmpeg -i ' + video_filename + ' 2>&1 | sed -n "s/.*, \\(.*\\) fp.*/\\1/p"'
    fps = subprocess.check_output(fps_cmd, shell=True).decode("utf-8").rstrip("\n")
    return outfile


def uploadframes(out_file, output_bucket):
    s3 = boto3.client('s3')
    file_path = '/tmp/' + out_file
    with open(file_path, 'rb') as file:
        s3.upload_fileobj(file, output_bucket, out_file)

    lambda_client = boto3.client('lambda')

    payload = {
        'bucket_name': output_bucket,
        'image_file_name': out_file
    }
    
    response = lambda_client.invoke(
        FunctionName = "face-recognition",
        InvocationType = 'Event',
        Payload = json.dumps(payload)
    )


def lambda_handler(event, context):
    try:
        input_bucket = '1230219135-input'
        output_bucket = "1230219135-stage-1"
        filename = event['Records'][0]['s3']['object']['key']
        s3 = boto3.client('s3')
        download_path = '/tmp/' + filename
        s3.download_file(input_bucket, filename, download_path) 
        out_file = video_splitting_cmdline(download_path)
        
        uploadframes(out_file=out_file, output_bucket=output_bucket)
        
        return {
        'statusCode': 200,
        'body': json.dumps('Video Splitting Successful...')
    }
    
    except Exception as e:
        logger.error("An error occured...%s", str(e))
        raise e
        
    
    