# Using Skypilot


## Using Skypilot with Prime Intellect Compute

Prime Intellect has pre-release support for Skypilot integration via a [fork](https://github.com/skypilot-org/skypilot/pull/5923) of the Skypilot repo. It requires some additional setup steps, but can nonetheless be used to launch clusters and experiments with your Prime Intellect account, from your laptop or any terminal. 

To install Skypilot from the Prime Intellect fork via `uv`:
```bash
uv tool install "skypilot[primeintellect] @ git+https://github.com/pokgak/skypilot.git@add-primeintellect-support"

# download the PI resource catalog 
mkdir ~/.sky/catalogs/v7/primeintellect/
curl -o ~/.sky/catalogs/v7/primeintellect/vms.csv https://raw.githubusercontent.com/pokgak/skypilot-catalog/refs/heads/add-primeintellect-catalog/catalogs/v7/primeintellect/vms.csv
```
Create a Prime Intellect [API key](https://app.primeintellect.ai/dashboard/tokens) with the following permissions:
- Instances: **Read and write**
- Availability: **Read only**
- SSH Keys: **Read and write**

Ensure that your local SSH public key is registered with your Prime Intellect [account](https://app.primeintellect.ai/dashboard/profile).

To configure credentials, create a file `~/.prime/config.json` with the following contents:
```json
{
    "api_key": "<YOUR_PI_API_KEY>",
    "team_id": "",
    "base_url": "https://api.primeintellect.ai",
    "ssh_key_path": "/Users/<user>/.ssh/name_of_your_registered_ssh_key_ed25519"
}
```
You should then be able to run `sky check primeintellect` and see:
```bash
$ sky check primeintellect
Checking credentials to enable infra for SkyPilot.
  Primeintellect: enabled [compute]

🎉 Enabled infra 🎉
  Primeintellect [compute]

To enable a cloud, follow the hints above and rerun: sky check
If any problems remain, refer to detailed docs at: https://docs.skypilot.co/en/latest/getting-started/installation.html

Using SkyPilot API server: http://127.0.0.1:46580
```

You can now use Skypilot normally, specifying `primeintellect` as the compute provider. Creating a cluster with a `sky launch` command should show the instance in your PI Instances dashboard.

Not all GPU providers available via `primeintellect` are configured to work seamlessly with Skypilot. We generally recommend using Nebius GPUs when possible

You can show available cluster configurations for a given GPU type (e.g. 1x H100) by running:
```bash
$ sky show-gpus --infra primeintellect H100:1

GPU   QTY  CLOUD           INSTANCE_TYPE                        DEVICE_MEM  vCPUs  HOST_MEM  HOURLY_PRICE  HOURLY_SPOT_PRICE  REGION             
H100  1    Primeintellect  massedcompute__1xH100_80GB__20__128  80GB        20     128GB     $ 1.890       $ 99999999.000     US - us-central-3  
H100  1    Primeintellect  hyperstack__1xH100_80GB__28__180     80GB        28     180GB     $ 1.900       $ 99999999.000     CA - CANADA-1      
H100  1    Primeintellect  nebius__1xH100_80GB__16__200         80GB        16     200GB     $ 2.118       $ 99999999.000     FI - eu-north1     
H100  1    Primeintellect  runpod__1xH100_80GB__16__188         80GB        16     188GB     $ 2.207       $ 99999999.000     UNSPECIFIED        
H100  1    Primeintellect  lambdalabs__1xH100_80GB__26__200     80GB        26     200GB     $ 2.490       $ 99999999.000     US - us-west-3     
H100  1    Primeintellect  runpod__1xH100_80GB__24__251         80GB        24     251GB     $ 2.707       $ 99999999.000     UNSPECIFIED        
H100  1    Primeintellect  runpod__1xH100_80GB__20__125         80GB        20     125GB     $ 3.007       $ 99999999.000     UNSPECIFIED        
H100  1    Primeintellect  lambdalabs__1xH100_80GB__26__225     80GB        26     225GB     $ 3.290       $ 99999999.000     US - us-south-2 
```

```bash
sky launch -c test-gpu --down --infra primeintellect -t nebius__1xH100_80GB__16__200
```

## Skypilot Usage

Docs: https://docs.skypilot.co/en/latest/docs/index.html


"Hello, World" test:
```bash
sky launch -c hello-world --down --infra primeintellect # launches minimal CPU cluster
sky exec hello-world echo "hello, world!" # prints "hello, world!"
sky down hello-world # tears down your cluster
```

GPU test:
```
sky launch -c test-gpu --down --infra primeintellect --gpus=H100:8