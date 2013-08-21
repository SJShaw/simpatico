/* Contains naming violations of different types. Currently contains
** 11
** violations. (includes filename)
*/

#define sillyMACRO(x)   (x)+(x) //violation
#define GOOD_MACRO(x)   (x)*(x)
#define DEFbad  //violation
#define GOOD_DEF
#define bool int /*actually good, but will be hard to test */

typedef struct bobStruct { /* violation */
    int thing;
} GoodStruct;

typedef struct Thing {
    int thing;
} badStruct; /* violation */

int a, B; /* violation */
char a_char; /* violation */

void FunctionBad(void) { /* violation */
}

void functionStuff(void) { /* violation */
}

void struct_var(bobStruct BobStruct) { /* violation  (var naming) */
}

void good_func(int a, char B) { /* violation (for B) */

}
