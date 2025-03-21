import json
import boto3
import os
import subprocess

s3_client = boto3.client('s3')

def video_splitting_cmdline(video_filename):
    filename = os.path.basename(video_filename)
    outfile = os.path.splitext(filename)[0] + ".jpg"
    output_path = f"/tmp/{outfile}"
    split_cmd = f'ffmpeg -i {video_filename} -vframes 1 {output_path}'
    try:
        print(f"Running frame extraction command: {split_cmd}")
        subprocess.check_call(split_cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print("Frame extraction failed.")
        print(f"Return code: {e.returncode}")
        print(f"Output: {e.output}")
        return None

    fps_cmd = f'ffmpeg -i {video_filename} 2>&1 | sed -n "s/.*, \\(.*\\) fp.*/\\1/p"'
    try:
        print(f"Running FPS extraction command: {fps_cmd}")
        fps = subprocess.check_output(fps_cmd, shell=True).decode("utf-8").rstrip("\n")
        print(f"FPS extracted: {fps}")
    except subprocess.CalledProcessError as e:
        print("FPS extraction failed.")
        print(f"Return code: {e.returncode}")
        print(f"Output: {e.output}")
        return None

    return outfile, fps


def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event, indent=2))
        
        if "Records" in event:
            input_bucket = event['Records'][0]['s3']['bucket']['name']
            input_key = event['Records'][0]['s3']['object']['key']
            print(f"Processing video from Bucket: {input_bucket}, Key: {input_key}")

            video_name = os.path.splitext(os.path.basename(input_key))[0]
            download_path = f"/tmp/{video_name}.mp4"
            
            print(f"Attempting to download {input_key} from bucket {input_bucket} to {download_path}")
            s3_client.download_file(input_bucket, input_key, download_path)
            print(f"Downloaded {input_key} to {download_path}")

            result = video_splitting_cmdline(download_path)
            if result is None:
                print("Failed to split video or extract FPS.")
                return {
                    'statusCode': 500,
                    'body': json.dumps('Video splitting or FPS extraction failed.')
                }

            outfile, fps = result
            print(f"Single frame extracted: {outfile}, FPS: {fps}")

            output_bucket = "1230219135-stage-1"
            output_folder = video_name
            frame_key = f"{output_folder}/{outfile}"
            frame_path = f"/tmp/{outfile}"

            try:
                s3_client.upload_file(frame_path, output_bucket, frame_key)
                print(f"Uploaded {outfile} to {output_bucket}/{frame_key}")
            except Exception as upload_error:
                print(f"Failed to upload {outfile} to {output_bucket}/{frame_key}: {upload_error}")
                return {
                    'statusCode': 500,
                    'body': json.dumps(f"Failed to upload frame {outfile} to S3.")
                }

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Video processed successfully.',
                    'fps': fps,
                    'frame_uploaded': frame_key
                })
            }

        else:
            print("No S3 record found in the event. Exiting.")
            return {
                'statusCode': 400,
                'body': json.dumps('No S3 event record found.')
            }

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'An unexpected error occurred during execution',
                'error': str(e)
            })
        }
