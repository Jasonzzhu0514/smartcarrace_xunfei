import os
import pandas as pd


detect_result_path = "/home/iflytek-car/gazebo_test_ws/src/gazebo_pkg/result/detect/"
category = {
    'yellow_pepper': 'Vegetable','tomato': 'Vegetable','potato': 'Vegetable',
    'banana': 'Fruit','watermelon': 'Fruit','apple': 'Fruit',
    'cola': 'Dessert','cake': 'Dessert','milk': 'Dessert'}

def posscess(target_category):
    latest_folder = get_latest_modified_folder(detect_result_path)
    df = pd.read_csv(detect_result_path + latest_folder + "/predictions.csv")
    df['Category'] = df['Prediction'].map(category)
    df['Room'] = df['Image Name'].str.extract(r'([A-Z])')

    room_dict = dict(zip(df['Room'], df['Prediction']))

    result_str = "Detect Result:\nRoom_A : {}. \nRoom_B : {}. \nRoom_C : {}.".format(
        room_dict.get('A', 'Unknown'),
        room_dict.get('B', 'Unknown'),
        room_dict.get('C', 'Unknown'))

    # print(result_str["Prediction"])
    filtered = df[df['Category'] == target_category]
    # print(filtered)
    detect_result = filtered[filtered['Room'] == filtered['Room'].tolist()[0]]['Prediction'].values[0]
    print(detect_result)


    return filtered['Room'].tolist()[0]

def get_latest_modified_folder(parent_path):
    folders = [os.path.join(parent_path, name) for name in os.listdir(parent_path)
               if os.path.isdir(os.path.join(parent_path, name))]
    if not folders:
        print("No folder.")
        return None
    latest_folder = max(folders, key=os.path.getmtime)
    return os.path.basename(latest_folder)

Room = posscess("Vegetable")

print(Room)
