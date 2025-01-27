import cv2
import os
import time
import shutil
import threading
import json

# Constants
width, video_height = 800, 600  # Window size
button_height = 100  # Space allocated for buttons
record_folder = None  # Global variable for the dataset folder

camera_index_list = [0,1,2,3,4,5]  # List of camera indices

with open("configuration.json", "r") as file:
    json_data = json.load(file)

camera_index_list = json_data["camera_index_list"]
time_delay = json_data["time_delay"] #time delay to take pictures

thread_list = []
start_capturing = False
run = True

# Function to get the next dataset folder name
def get_next_dataset_folder():
    dataset_count = 1
    while os.path.exists(f"datasets/dataset_{dataset_count}"):
        dataset_count += 1
    return f"datasets/dataset_{dataset_count}"

# Create a new dataset folder
def create_dataset(camera_id):
    global record_folder
    camera_id = str(camera_id)
    if record_folder is None:
        record_folder = get_next_dataset_folder()
        os.makedirs(record_folder, exist_ok=True)
        print(f"Created dataset folder: {record_folder}")
    try:
        if not os.path.isdir(record_folder + "/" + camera_id):
            os.makedirs(record_folder + "/" + camera_id, exist_ok=True)
            print(f"Created camera ID folder: {record_folder}/{camera_id}")
    except Exception as e:
        print("Error creating dataset folder: " + str(e))

# Save a snapshot
def save_snapshot(camera_id, frame):
    create_dataset(camera_id)
    global record_folder
    camera_id = str(camera_id)
    if record_folder and os.path.isdir(record_folder + "/" + camera_id):
        filename = os.path.join(record_folder + "/" + camera_id, f'snapshot_{int(time.time())}.jpg')
        cv2.imwrite(filename, frame)
        print(f"Snapshot saved: {filename}")
    else:
        print("No dataset folder exists. Please create a dataset first.")

# Merge datasets
def merge_datasets():
    common_folder = 'datasets/common_dataset'
    os.makedirs(common_folder, exist_ok=True)
    dataset_folders = [folder for folder in os.listdir('./datasets') if os.path.isdir(folder) and folder.startswith('dataset_')]
    for folder in dataset_folders:
        for file in os.listdir(f"./datasets/{folder}"):
            src = os.path.join(f"./datasets/{folder}", file)
            dst = os.path.join(common_folder, f'{folder}_{file}')
            shutil.copy2(src, dst)
    print(f"All datasets merged into '{common_folder}'.")

# Main function for each camera
def main_program(camera_id, camera):
    global start_capturing, run

    previous_time = time.time() * 1000
    current_time = previous_time

    print(f"Starting camera {camera_id}")
    window_name = f"Camera id: {camera_id} index: {camera_index_list.index(camera_id)}"+" - S-Start, Q-quit"

    while run:
        ret, frame = camera.read()
        if not ret:
            print(f"Failed to grab frame for Camera {camera_id}.")
            break

        # Display the video feed
        cv2.imshow(window_name, frame)

        # Check for key inputs
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):  # Quit the stream
            print(f"Closing Camera {camera_id}.")
            run = False
            start_capturing = False
            break
        elif key == ord('c'):  # Create dataset
            create_dataset(camera_id)
        elif key == ord('s'):  # Save snapshot
            print("Capturing Started")
            start_capturing = True
            # save_snapshot(camera_id, frame)
        elif key == ord('m'):  # Merge datasets
            merge_datasets()

        if start_capturing:
            current_time = time.time() * 1000
            if(previous_time + time_delay < current_time):
                previous_time = current_time
                save_snapshot(camera_id, frame)

    # Cleanup
    camera.release()
    cv2.destroyWindow(window_name)

# Start threads for each camera
for camera_id in camera_index_list:
    try:
        camera = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
        if not camera.isOpened():
            print(f"Error: Could not open camera {camera_id}.")
            continue
        t = threading.Thread(target=main_program, args=(camera_id, camera,))
        thread_list.append(t)
        t.start()
    except Exception as e:
        print(f"Error initializing camera {camera_id}: {e}")

# Wait for threads to complete
for t in thread_list:
    t.join()

print("All camera streams closed.")
