from ultralytics import YOLO
import openvino, sys, shutil, os

model_path = "/Users/kushal/intel/best.pt"
model_type = 'yolo_v8'

model = YOLO(model_path)
model.info()

print("Exporting model to OpenVINO IR format...")
converted_path = model.export(format='openvino')

converted_model = os.path.join(converted_path, os.path.basename(model_path).replace('.pt', '.xml'))
core = openvino.Core()
ov_model = core.read_model(model=converted_model)
if model_type in ["YOLOv8-SEG", "yolo_v11_seg"]:
    print("Seg model-------------")
    ov_model.output(0).set_names({"boxes"})
    ov_model.output(1).set_names({"masks"})

ov_model.set_rt_info(model_type, ['model_info', 'model_type'])

os.makedirs("FP32", exist_ok=True)
os.makedirs("FP16", exist_ok=True)

openvino.save_model(ov_model, f'./FP32/{os.path.basename(model_path).replace(".pt", ".xml")}', compress_to_fp16=False)
openvino.save_model(ov_model, f'./FP16/{os.path.basename(model_path).replace(".pt", ".xml")}', compress_to_fp16=True)

shutil.rmtree(converted_path)

print(f"✅ Model conversion complete! OpenVINO IR model saved in FP32 and FP16 formats.")
