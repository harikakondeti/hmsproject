import random
def genotp():
    u_c=[chr(i) for i in range(ord('A'),ord('Z')+1)]
    L_c=[chr(i) for i in range(ord('a'),ord('z')+1)]
    otp=''
    for i in range(2):
        otp+=random.choice(u_c)
        otp+=str(random.randint(0,9))
        otp+=random.choice(L_c)
    return otp
