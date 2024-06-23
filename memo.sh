sudo yum install -y docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -a -G docker ec2-user
sudo yum install -y git make
git clone https://github.com/TakeshiAkehi/zmk-lambda.git
source load_constants
make build
exit