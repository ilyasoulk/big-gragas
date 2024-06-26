# How to launch the project:

1. Move the bourse dir of this repo on your home directory :  ~
2. Download the boursorama.tar : https://www.lrde.epita.fr/~ricou/pybd/projet/boursorama.tar
3. Run this command :

```
cd /srv/libvirt-workdir && mkdir data && cd data && tar -xvf ~/Downloads/boursorama.tar && rm ~/Downloads/boursorama.tar &&
cd ~/bourse/docker/analyzer && make fast &&
cd ~/bourse/docker/dashboard && make fast
```

4. Open a terminal and run this command : `cd ~/bourse/docker/ && docker compose up db`
5. Open a terminal and run this command : `cd ~/bourse/docker/ && docker compose up analyzer`
6. If you are on a PC with 16 cores, the waiting time should be less than`30 MINUTES` (we managed to do it in 13 minutes). While waiting, please delete any useless window/terminal (like firefox) to save some memory.
7. Open a terminal and run this command : `cd ~/bourse/docker/ && docker compose up dashboard`
8. Go to the `localhost:8050`


# Cleaning: Here is a resume of every cleaning process that we did on the given data  ###

1. Verifying and dropping the None and NaN value of our dataFrames
2. Verifying if some companies did not change their names in 5 years and edit the name like LNC which became BASSAC
3. Verifying if the symbol column and symbol header are exaclty the same
4. Checking if the 'last' format is correct (positive float) && Changing the value that does not match the format such as the ones that ends with a '(c)' or a '(s)'
     - End with (c) : There is nothing to convert or anything, it just to signal that the value can be convertible or is a cum_dividend
     - End with (s) : There is nothing to convert or anything, it just to signal that the value is a subscription right/subscription warrant
5. Checking if the 'volume' format is correct (positive integer) && Dropping every volume value that are negative such as the value from the XXX company or the XXX company
6. Checking if the 'name' format is correct (all caps) && Edit the names that are not alike Ex:  'PLASTiVALOIRE' != 'PLASTIVALOIRE' (only one found)
7. Checking if the 'date' format is correct : YYYY-MM-DD HH:MM:SS.microsecondes with YYYY = name of the dir
8. Checking if the 'symbol' format is correct
9. Drop the duplicates if there is any

Note:
After a discussion with an assistant, we don't really have to verify the outliers because big variation of values is something that is normal in the bourse area

# Strategy to fill the DB in less than 30 minutes (13 min for us):

What have we done in order to do that:

1. The code work with batches, in order to avoid to use a too large amount of memory
2. We use parallel programming to make it faster
3. We also do some important cleaning while operating, such as deleting rows where the volume is equal to 0.
4. We change the encoding of integer columns. For example, df['mid'] = df['mid'].astype('Int8'), here the number is only 8-bits.
5. We take care of the companies before stock and daystock
