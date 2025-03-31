# import os
# import random
# import shutil
# import hashlib
# from PIL import Image
# import torchvision.transforms as transforms

# # Paths
# dataset_path = "/content/skin-disease-dataset/"
# train_path = os.path.join(dataset_path, "train_set")
# test_path = os.path.join(dataset_path, "test_set")

# # Target count
# TARGET_TRAIN = 80
# TARGET_TEST = 20

# # Augmentation for low-count classes
# augment = transforms.Compose([
#     transforms.RandomHorizontalFlip(),
#     transforms.RandomRotation(10),
#     transforms.ColorJitter(brightness=0.2, contrast=0.2),
#     transforms.RandomAffine(degrees=10, translate=(0.1, 0.1)),
#     transforms.ToTensor()
# ])

# def get_image_hash(image_path):
#     """Returns hash of an image file to detect duplicates."""
#     with open(image_path, "rb") as f:
#         return hashlib.md5(f.read()).hexdigest()

# def remove_duplicates(directory):
#     """Removes duplicate images from a directory."""
#     seen_hashes = set()
#     for class_name in os.listdir(directory):
#         class_dir = os.path.join(directory, class_name)
#         if os.path.isdir(class_dir):
#             for img in os.listdir(class_dir):
#                 img_path = os.path.join(class_dir, img)
#                 if img.endswith(('.png', '.jpg', '.jpeg')):
#                     img_hash = get_image_hash(img_path)
#                     if img_hash in seen_hashes:
#                         os.remove(img_path)  # Delete duplicate
#                     else:
#                         seen_hashes.add(img_hash)

# def augment_image(image_path, save_dir, count):
#     """Generates augmented images to increase class size."""
#     image = Image.open(image_path)
#     for i in range(count):
#         augmented_img = augment(image)
#         augmented_img = transforms.ToPILImage()(augmented_img)
#         augmented_img.save(os.path.join(save_dir, f"aug_{i}_{os.path.basename(image_path)}"))

# def balance_class(class_name, class_dir, target_count):
#     """Ensures each class has exactly `target_count` images."""
#     images = os.listdir(class_dir)
#     images = [img for img in images if img.endswith(('.png', '.jpg', '.jpeg'))]
    
#     if len(images) > target_count:  # Reduce
#         selected_images = random.sample(images, target_count)
#         for img in images:
#             if img not in selected_images:
#                 os.remove(os.path.join(class_dir, img))
    
#     elif len(images) < target_count:  # Augment
#         needed = target_count - len(images)
#         for _ in range(needed):
#             random_img = random.choice(images)
#             augment_image(os.path.join(class_dir, random_img), class_dir, 1)

# # Step 1: Remove Duplicates
# print("🧹 Removing duplicate images...")
# remove_duplicates(train_path)
# remove_duplicates(test_path)

# # Step 2: Balance Dataset
# print("⚖️ Balancing dataset...")
# for dataset_type, target in [("train_set", TARGET_TRAIN), ("test_set", TARGET_TEST)]:
#     dataset_dir = os.path.join(dataset_path, dataset_type)
    
#     for class_name in os.listdir(dataset_dir):
#         class_dir = os.path.join(dataset_dir, class_name)
#         if os.path.isdir(class_dir):
#             balance_class(class_name, class_dir, target)

# print("✅ Dataset cleaning & balancing complete!")
