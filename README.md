# Survey cleaning
This is a simple project for the interview process

## Usage
To build the docker image and run it simply execute:
```make``` in the project directory

In order to only build the image execute:
```make build```

In order to run image without build execute:
```make run```

Please make sure to have docker installed

To run the script in your local python environment please make sure every 
required package included in requirements.txt is installed or install it 
executing: 
```pip install -r requirements.txt```
or 
```conda install --file requirements.txt```

and start the script by:
```python main.py```

After successful cleaning file final_output.csv should be created in 
data/output directory and success message should be prompted
