# coding=utf-8
import torch.autograd
import torch.nn as nn
from torchvision import transforms
from torchvision import datasets
from torchvision.utils import save_image
import os

# 创建文件夹
if not os.path.exists('./img_AE'):
    os.mkdir('./img_AE')
# GPU
device = 'cuda' if torch.cuda.is_available() else 'cpu'
batch_size = 128
num_epoch = 20
z_dimension = 2
# 图形啊处理过程
img_transform = transforms.Compose([
    transforms.ToTensor(),
])
# mnist dataset mnist数据集下载
mnist = datasets.MNIST(
    root='../data/', train=True, transform=img_transform, download=True
)

# data loader 数据载入
dataloader = torch.utils.data.DataLoader(
    dataset=mnist, batch_size=batch_size, shuffle=True
)


# 定义AE的模型，包含Decoder和Encoder两个部分
class autoencoder(nn.Module):
    def __init__(self):
        super(autoencoder, self).__init__()
        # 定义编码器
        self.encoder = nn.Sequential(
            nn.Conv2d(1, 16, 3, 2, 1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.Conv2d(16, 32, 3, 2, 1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 16, 3, 1, 1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
        )
        self.encoder_fc = nn.Linear(16 * 7 * 7, z_dimension)
        self.decoder_fc = nn.Linear(z_dimension, 16 * 7 * 7)
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(16, 16, 4, 2, 1),
            nn.BatchNorm2d(16),
            nn.Tanh(),
            nn.ConvTranspose2d(16, 1, 4, 2, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        x = self.encoder(x)
        x = x.view(x.shape[0], -1)
        code = self.encoder_fc(x)
        x = self.decoder_fc(code)
        x = x.view(x.shape[0], 16, 7, 7)
        decode = self.decoder(x)
        return code, decode


# 创建对象
AE = autoencoder().to(device)
# 如果不是第一次运行，可以加载之前运行的模型
# AE.load_state_dict(torch.load('./AE.pth'))
# 是单目标二分类交叉熵函数
criterion = nn.BCELoss()
ae_optimizer = torch.optim.Adam(AE.parameters(), lr=0.0003)
###########################进入训练##判别器的判断过程#####################
for epoch in range(num_epoch):  # 进行多个epoch的训练
    for i, (img, _) in enumerate(dataloader):
        num_img = img.size(0)
        # view()函数作用把img变成[batch_size,channel_size,784]
        img = img.view(num_img, 1, 28, 28).to(device)  # 将图片展开为28*28=784
        code, recon_img = AE(img)  # 将真实图片放入判别器中
        loss = criterion(recon_img, img)
        ae_optimizer.zero_grad()  # 在反向传播之前，先将梯度归0
        loss.backward()  # 将误差反向传播
        ae_optimizer.step()  # 更新参数
        if (i + 1) % 100 == 0:
            print('Epoch[{}/{}],ae_loss:{:.6f} '.format(
                epoch, num_epoch, loss.item(),
            ))
        if epoch == 0:
            real_images = img.cpu().data.clamp(0, 1)
            save_image(real_images, './img_AE/real_images.png')
        if i == len(dataloader) - 1:
            fake_images = recon_img.cpu().data.clamp(0, 1)
            save_image(fake_images, './img_AE/fake_images-{}.png'.format(epoch + 1))
# 保存模型
torch.save(AE.state_dict(), './AE_z2.pth')
