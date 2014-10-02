# Install Python 3 on Moss

1. Download Python 3.4.1:
    ```
    wget http://python.org/ftp/python/3.4.1/Python-3.4.1.tgz
    ```

2. Extract:
    ```
    tar xvfz Python-3.4.1.tgz
    ```

3. Configure and Install:
    ```
    cd Python-3.4.1
    ./configure --prefix=$HOME/python3.4
    make && make install
    ```

4. Test if it worked:
    ```
    which python3
    ```