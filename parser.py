#!/usr/bin/python3
# Gregory Smith     b00095534
# Joseph Press      b00095348

# TODO
def parse(contents):
    return contents

def main() -> int:
    i = 1
    outputs_lst = []
    while True: # loop until file open fails
        try:
            f=open(str(i)+'.txt','r')
        except FileNotFoundError:
            # write the output and terminate
            out = open('parser_output.txt','w')
            out.write('\n'.join(outputs_lst))
            return 0
        # read and parse the contents of the file
        contents = f.read()
        output = parse(contents)
        outputs_lst.append(str(i)+".txt:\n"+output)
        i+=1
    return 0

if __name__=="__main__":
    exit(main())
