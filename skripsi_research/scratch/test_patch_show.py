import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

captured_images = []
orig_show = plt.show

def custom_show(*args, **kwargs):
    for num in plt.get_fignums():
        fig = plt.figure(num)
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format='png', dpi=100, bbox_inches='tight')
        img_buf.seek(0)
        captured_images.append(base64.b64encode(img_buf.read()).decode('utf-8'))
    orig_show(*args, **kwargs)

plt.show = custom_show

plt.plot([1, 2, 3], [4, 5, 6])
plt.title("Test")
plt.show()

print("Captured images count:", len(captured_images))
print("First 50 chars of b64:", captured_images[0][:50])
