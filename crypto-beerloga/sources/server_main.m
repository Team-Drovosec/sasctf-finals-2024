#import <Foundation/Foundation.h>
#include "pr.pb-c.h"
#include <unistd.h>
#include <fcntl.h>
#include <gmp.h>
#include <libpq-fe.h>

#include "sha1.h"

void get_random_safe_number(mpz_t p, size_t bits) {
    FILE *f;
    if (bits < 3 || !(f = fopen("/dev/random", "rb"))) return ;
    size_t nbytes = (bits+7)>>3;
    uint8_t buf[nbytes];
    if (fread(buf, 1, nbytes, f) != nbytes) exit(1);
    mpz_import(p, nbytes, 1, 1, 0, 0, buf);

    fclose(f);
}

#define PAGE_SIZE 20

enum Commands {
	REGISTER,
	LOGIN_REQUEST_CHALLENGE,
	LOGIN_SEND_RESPONSE,
	RESERVED0,
	LIST_BEERS,
	RESERVED1,
	ADD_BEER,
	ADD_COMMENT,
	ADD_PRIVATE_MESSAGE,
	LIST_COMMENTS,
	RESERVED2,
	RESERVED3,
	DELETE_COMMENT,
	RESERVED4,
	RESERVED5,
    GET_USER_INFO
};

enum CommandType {

    REQUEST,
    RESPONSE,
    ERROR
};

@interface Cryptography:NSObject {

}

+(void)generateRandomPrime: (mpz_t) outputNumber paramBits:(size_t) bits;

+(void)generateRandomPrimeInRange: (mpz_t) outputNumber paramBits:(size_t) bits  paramCap:(mpz_t) cap;

+(void)generateRandomInRange: (mpz_t) outputNumber paramBits:(size_t) bits  paramCap:(mpz_t) cap;

@end

@implementation Cryptography {
}

-(id)init {
    self = [super init];
    return self;
}
-(void) dealloc {
    [super dealloc];
}
+(void)generateRandomPrime: (mpz_t) outputNumber paramBits:(size_t) bits {
    mpz_t q;
    mpz_init(q);
    get_random_safe_number(q, bits);
    mpz_nextprime(outputNumber, q);

    return ;
}

+(void)generateRandomInRange: (mpz_t) outputNumber paramBits:(size_t) bits  paramCap:(mpz_t) cap {
    mpz_t gener;
    mpz_init(gener);
    get_random_safe_number(gener, bits);
    mpz_mod(outputNumber, gener, cap);
    return ;
}

+(void)generateRandomPrimeInRange: (mpz_t) outputNumber paramBits:(size_t) bits  paramCap:(mpz_t) cap {
    mpz_t q;
    mpz_init(q);
    get_random_safe_number(q, bits);
    mpz_t q1;
    mpz_init(q1);
    mpz_mod(q1, q, cap);
    mpz_nextprime(outputNumber, q1);

}
@end

void sign_message(NSString *message, mpz_t n, mpz_t gamma, mpz_t q, mpz_t alpha, mpz_t a, mpz_t s, mpz_t sigma, mpz_t lambda) {
    const char *message_utf8 = strdup([message UTF8String]);

    mpz_t k;
    mpz_init(k);
    [Cryptography generateRandomInRange:k paramBits:1024 paramCap:q];

    mpz_powm(sigma, gamma, k, n);

    uint8_t sigma_bytes[1024 * 8] = {0};
    size_t sigma_bytes_count = 1024 * 8;
    mpz_export(sigma_bytes, &sigma_bytes_count, 1, 1, 0, 0, sigma);

    SHA1_CTX sha; uint8_t sha_hash_results[20];
    SHA1Init(&sha);

    SHA1Update(&sha, (uint8_t *)message_utf8, strlen(message_utf8));

    SHA1Update(&sha, (uint8_t *)sigma_bytes, 1024 * 8);

    SHA1Final(sha_hash_results, &sha);

    mpz_t e;
    mpz_init(e);
    mpz_import(e, 20, 1, 1, 0, 0, sha_hash_results);

    mpz_t product;
    mpz_init(product);
    mpz_mul(product, a, e);
    mpz_t x;
    mpz_init(x);
    mpz_sub(x, k, product);

    mpz_t l;
    mpz_init(l);

    mpz_fdiv_qr(l, s, x, q);

    mpz_powm(lambda, gamma, l, n);

}

bool verify_message(NSString *message, mpz_t group_n, mpz_t gamma, mpz_t q, mpz_t alpha, mpz_t s, mpz_t sigma, mpz_t lambda) {
    const char *message_utf8 = strdup([message UTF8String]);
    uint8_t sigma_bytes[1024 * 8] = {0};
    size_t sigma_bytes_count = 1024 * 8;
    mpz_export(sigma_bytes, &sigma_bytes_count, 1, 1, 0, 0, sigma);

    SHA1_CTX sha; uint8_t sha_hash_results[20];
    SHA1Init(&sha);

    SHA1Update(&sha, (uint8_t *)message_utf8, strlen(message_utf8));

    SHA1Update(&sha, (uint8_t *)sigma_bytes, 1024 * 8);

    SHA1Final(sha_hash_results, &sha);

    mpz_t e;
    mpz_init(e);
    mpz_import(e, 20, 1, 1, 0, 0, sha_hash_results);

    mpz_t power1;
    mpz_init(power1);
    mpz_powm(power1, gamma, s, group_n);

    mpz_t power2;
    mpz_init(power2);
    mpz_powm(power2, alpha, e, group_n);

    mpz_t power3;
    mpz_init(power3);
    mpz_powm(power3, lambda, q, group_n);

    mpz_t mul;
    mpz_init(mul);
    mpz_mul(mul, power1, power2);
    mpz_mod(mul, mul, group_n);
    mpz_mul(mul, mul, power3);
    mpz_mod(mul, mul, group_n);

    if (!mpz_cmp(mul, sigma)) {
        return true;
    }
    return false;
}

@interface User:NSObject {
	@public NSString *_userName;
	@public mpz_t _group_n;
	@public mpz_t _gamma;
	@public mpz_t _q;
	@public mpz_t _a;
	@public mpz_t _alpha;

}

+(User *)registerUser: (NSString *) nickname;
-(void)authenticateAs: (NSString *) nickname group_n : (char *)group_n gamma: (char *) gamma q: (char *) q alpha: (char *) alpha;

@end

@implementation User {
}

-(id)init {
    self = [super init];
    _userName = @"";
    mpz_init(_group_n);
    mpz_init(_gamma);
    mpz_init(_q);
    mpz_init(_a);
    mpz_init(_alpha);

    return self;
}

-(id)initWithCryptoParams: (NSString *)userName groupN : (mpz_t)arg_group_n gamma : (mpz_t)arg_gamma q : (mpz_t)arg_q a : (mpz_t)arg_a alpha : (mpz_t)arg_alpha  {
    self = [self init];
    _userName = [[NSString alloc] initWithString:userName];
    mpz_init_set(_group_n, arg_group_n);
    mpz_init_set(_gamma, arg_gamma);
    mpz_init_set(_q, arg_q);
    mpz_init_set(_a, arg_a);
    mpz_init_set(_alpha, arg_alpha);
    return self;
}

-(void)assignCryptoParams: (NSString *)userName groupN : (mpz_t)arg_group_n gamma : (mpz_t)arg_gamma q : (mpz_t)arg_q a : (mpz_t)arg_a alpha : (mpz_t)arg_alpha  {
    _userName = [[NSString alloc] initWithString:userName];
    mpz_init_set(_group_n, arg_group_n);
    mpz_init_set(_gamma, arg_gamma);
    mpz_init_set(_q, arg_q);
    mpz_init_set(_a, arg_a);
    mpz_init_set(_alpha, arg_alpha);
    return;
}

-(void) authenticateAs: (NSString *) nickname group_n : (char *)group_n gamma: (char *) gamma q: (char *) q alpha: (char *) alpha {
    _userName = [nickname copy];

    mpz_set_str(_group_n, group_n, 10);
    mpz_set_str(_gamma, gamma, 10);
    mpz_set_str(_q, q, 10);
    mpz_set_str(_alpha, alpha, 10);

}
-(void) dealloc {
    [super dealloc];
}
+(User *)registerUser: (NSString *) nickname {
    if ([nickname isEqualToString:@""]) {
        return NULL;
    }

    mpz_t group_n;
    mpz_init(group_n);
    [Cryptography generateRandomPrime:group_n paramBits:1024];
    char *tmp = mpz_get_str(NULL,10,group_n);
    NSString *str = [NSString stringWithUTF8String: tmp];

    mpz_t gamma;
    mpz_init(gamma);

    [Cryptography generateRandomPrimeInRange:gamma paramBits:1024 paramCap:group_n];

    tmp = mpz_get_str(NULL,10,gamma);
    str = [NSString stringWithUTF8String: tmp];

    mpz_t q;
    mpz_init(q);
    [Cryptography generateRandomPrime:q paramBits:160];

    tmp = mpz_get_str(NULL,10,q);
    str = [NSString stringWithUTF8String: tmp];

    mpz_t a;
    mpz_init(a);
    [Cryptography generateRandomPrimeInRange:a paramBits:1024 paramCap:q];

    tmp = mpz_get_str(NULL,10,a);
    str = [NSString stringWithUTF8String: tmp];

    mpz_t alpha;
    mpz_init(alpha);
    mpz_powm(alpha, gamma, a, group_n);

    tmp = mpz_get_str(NULL,10,alpha);
    str = [NSString stringWithUTF8String: tmp];

    User *user = [[User alloc] initWithCryptoParams:nickname groupN:group_n gamma:gamma q:q a:a alpha:alpha];
    return user;
}

@end

@interface VerificationContext:NSObject {
    @public NSString *nickname;
    @public mpz_t group_n;
	@public mpz_t sigma;
	@public mpz_t e;
	@public mpz_t gamma;
	@public mpz_t q;
	@public mpz_t alpha;
	@public BOOL exists;

}

@end

@implementation VerificationContext {
}
-(id)init {
	   self = [super init];
	   nickname = @"";
	   mpz_init(group_n);
	   mpz_init(sigma);
	   mpz_init(e);
	   mpz_init(gamma);
	   mpz_init(alpha);
	   exists = false;
	   return self;
}

@end

@interface Database:NSObject {

@public PGconn* conn;

}
@end

@implementation Database {
}
-(id)init {

    self = [super init];
    conn = PQconnectdb("user=postgres password=123 host=127.0.0.1 dbname=beerloga");
    if (!conn) {

    }
    else {

    }
    return self;
 }

-(BOOL)registerUser: (char *)userName n : (char *)n gamma : (char *)gamma q : (char *)q alpha : (char *)alpha {
    const char *query = "INSERT into users(username, n, gamma, q, alpha, timestamp) values ($1, $2, $3, $4, $5, now())";
    const char *params[5];
    params[0] = userName;
    params[1] = n;
    params[2] = gamma;
    params[3] = q;
    params[4] = alpha;
    PGresult* res = PQexecParams(conn, query, 5, NULL, params, NULL, NULL, 0);
    if(PQresultStatus(res) != PGRES_COMMAND_OK) {

        return false;
    }
    return true;
 }

 -(GetUserDetailsResponse *)getUserDetails: (char *) userName page: (int)page {
    const char *query = "SELECT n, gamma, q, alpha FROM users WHERE username = $1";
    const char *params1[1];
    params1[0] = userName;
    page -= 1;
    PGresult* res = PQexecParams(conn, query, 1, NULL, params1, NULL, NULL, 0);
    if(PQresultStatus(res) != PGRES_TUPLES_OK) {

        return NULL;
    }

    if (PQntuples(res) == 0) {
        return 0;
    }

    GetUserDetailsResponse *out_resp = calloc(1, sizeof(GetUserDetailsResponse));
    get_user_details_response__init(out_resp);
    out_resp->nickname = strdup(userName);
    out_resp->group_n = strdup(PQgetvalue(res, 0, 0));
    out_resp->gamma = strdup(PQgetvalue(res, 0, 1));
    out_resp->q = strdup(PQgetvalue(res, 0, 2));
    out_resp->alpha = strdup(PQgetvalue(res, 0, 3));

    const char *comments_count_query = "SELECT COUNT(*) FROM comments WHERE comment_author = $1 and is_private = false";
    const char *comments_count_query_params[1];
    comments_count_query_params[0] = userName;

    res = PQexecParams(conn, comments_count_query, 1, NULL, params1, NULL, NULL, 0);

    if(PQresultStatus(res) != PGRES_TUPLES_OK) {

        return NULL;
    }

    int num_comments = atoi(PQgetvalue(res, 0, 0));
    out_resp->pages_count = (num_comments / PAGE_SIZE) + (num_comments % PAGE_SIZE != 0);

    char *main_query = "SELECT comment_id, comment_value, comment_author, s, sigma, lambda, is_private, beer_id FROM comments WHERE comment_author = $1 and is_private = false OFFSET $2 LIMIT $3";
    const char *params[3];

    params[0] = userName;

    char str2[4096] = {0};
    snprintf(str2, 4096, "%d", PAGE_SIZE * page);
    params[1] = str2;

    char str3[4096] = {0};
    snprintf(str3, 4096, "%d", PAGE_SIZE);
    params[2] = str3;
    PGresult* main_res = PQexecParams(conn, main_query, 3, NULL, params, NULL, NULL, 0);

    if(PQresultStatus(main_res) != PGRES_TUPLES_OK) {

        return NULL;
    }

    out_resp->current_page = page + 1;
    int nrows = PQntuples(main_res);

    Comment **comments = calloc(nrows, sizeof(Comment *));

    for (int i = 0; i < nrows; i++) {
        comments[i] = calloc(1, sizeof(Comment));
        comment__init(comments[i]);

        comments[i]->comment_id = atoi(PQgetvalue(main_res, i, 0));
        comments[i]->comment_value = strdup(PQgetvalue(main_res, i, 1));
        comments[i]->comment_author = strdup(PQgetvalue(main_res, i, 2));
        comments[i]->s = strdup(PQgetvalue(main_res, i, 3));
        comments[i]->sigma = strdup(PQgetvalue(main_res, i, 4));
        comments[i]->lambda = strdup(PQgetvalue(main_res, i, 5));

        comments[i]->is_private = strdup(PQgetvalue(main_res, i, 6));
        comments[i]->beer_id = atoi(strdup(PQgetvalue(main_res, i, 7)));

    }
    out_resp->n_comments = nrows;
    out_resp->comments = comments;

    return out_resp;
 }

 -(uint32_t)addBeer: (const char *)beerName beerCreator : (const char *)beerCreator {
    const char *query = "INSERT into beers(beer_name, beer_creator, timestamp) values ($1, $2, now()) RETURNING beer_id";
    const char *params[5];
    params[0] = beerName;
    params[1] = beerCreator;

    PGresult* res = PQexecParams(conn, query, 2, NULL, params, NULL, NULL, 0);
    if(PQresultStatus(res) != PGRES_TUPLES_OK) {

        return 0;
    }

    int num_entries = PQntuples(res);
    if (num_entries != 0) {
        return atoi(PQgetvalue(res, 0, 0));
    }
    return 0;
 }

- (BOOL) userExists: (const char *) nickname {
    const char *query = "SELECT user_id FROM users WHERE username = $1";
    const char *params[1];
    params[0] = nickname;
     PGresult* query_res = PQexecParams(conn, query, 1, NULL, params, NULL, NULL, 0);
    if(PQresultStatus(query_res) != PGRES_TUPLES_OK) {

        return false;
    }

    int num_entries = PQntuples(query_res);
    if (num_entries != 0) {
        return true;
    }
    return false;

}

- (BOOL) deleteComment: (uint32_t) comment_id {
    const char *query = "DELETE FROM comments WHERE comment_id = $1";
    const char *params[1];
    char str[4096] = {0};
    snprintf(str, 4096, "%d", comment_id);
    params[0] = str;
     PGresult* query_res = PQexecParams(conn, query, 1, NULL, params, NULL, NULL, 0);
    if(PQresultStatus(query_res) != PGRES_COMMAND_OK) {

        return false;
    }

    return true;

}

  -(ListBeersResponse *)listBeers: (uint32_t) pageNumber {

    const char *count_query = "SELECT COUNT(*) from beers";

    PGresult* count_res = PQexecParams(conn, count_query, 0, NULL, NULL, NULL, NULL, 0);
    if(PQresultStatus(count_res) != PGRES_TUPLES_OK) {

        return NULL;
    }

    char *entries_count = PQgetvalue(count_res, 0, 0);

    const char *query = "SELECT * from beers ORDER BY beer_id DESC OFFSET $1 LIMIT 20";
    const char *params[1];
    char str[4096] = {0};
    snprintf(str, 4096, "%d", pageNumber * PAGE_SIZE);
    params[0] = str;
    PGresult* res = PQexecParams(conn, query, 1, NULL, params, NULL, NULL, 0);

    if(PQresultStatus(res) != PGRES_TUPLES_OK) {

        return NULL;
    }
    int nrows = PQntuples(res);
    ListBeersResponse *out_resp = calloc(1, sizeof(ListBeersResponse));
    list_beers_response__init(out_resp);
    Beer **beers = calloc(nrows, sizeof(Beer *));

    for (int i = 0; i < nrows; i++) {
        beers[i] = calloc(1, sizeof(Beer));
        beer__init(beers[i]);

        beers[i]->beer_id = atoi(PQgetvalue(res, i, 0));
        beers[i]->beer_name = strdup(PQgetvalue(res, i, 1));
        beers[i]->beer_creator = strdup(PQgetvalue(res, i, 2));

    }
    out_resp->number_pages = (atoi(entries_count) / PAGE_SIZE) + (atoi(entries_count) % PAGE_SIZE != 0);
    out_resp->page_number = pageNumber + 1;
    out_resp->n_beers = nrows;
    out_resp->beers = beers;

    return out_resp;
 }

 -(bool)doesBeerExist: (uint32_t) beerID {
    const char *count_query = "SELECT COUNT(*) from beers where beer_id = $1";
    const char *params[1];
    char str[4096] = {0};
    snprintf(str, 4096, "%d", beerID);

    params[0] = str;
    PGresult* count_res = PQexecParams(conn, count_query, 1, NULL, params, NULL, NULL, 0);
    if(PQresultStatus(count_res) != PGRES_TUPLES_OK) {

        return false;
    }

    char *entries_count = PQgetvalue(count_res, 0, 0);

    if (!strcmp(entries_count, "0")) {
        return false;
    }
    return true;
 }

 -(char *)getBeerOwner: (uint32_t) beerID {
    const char *query = "SELECT beer_creator FROM beers WHERE beer_id = $1";
    const char *params[1];
    char str[4096] = {0};
    snprintf(str, 4096, "%d", beerID);
    params[0] = str;
    PGresult* res = PQexecParams(conn, query, 1, NULL, params, NULL, NULL, 0);
    if(PQresultStatus(res) != PGRES_TUPLES_OK) {

        return NULL;
    }

    int nrows = PQntuples(res);
    if (nrows == 0) {
        return NULL;
    }
    char *owner = PQgetvalue(res, 0, 0);
    return strdup(owner);

 }

  -(char *)getCommentOwner: (uint32_t) commentID {
    const char *query = "SELECT comment_author FROM comments WHERE comment_id = $1";
    const char *params[1];
    char str[4096] = {0};
    snprintf(str, 4096, "%d", commentID);
    params[0] = str;
    PGresult* res = PQexecParams(conn, query, 1, NULL, params, NULL, NULL, 0);
    if(PQresultStatus(res) != PGRES_TUPLES_OK) {

        return NULL;
    }

    int nrows = PQntuples(res);
    if (nrows == 0) {
        return NULL;
    }
    char *owner = PQgetvalue(res, 0, 0);
    return strdup(owner);

 }

-(ListCommentsResponse *) getComments: (uint32_t) beerID page: (uint32_t) page requestingUser: (const char *) requestingUser isOwner: (bool) isOwner {
    PGresult *count_res = NULL;
    PGresult *main_res = NULL;
    page -= 1;
    if (isOwner) {

        char *count_query = "SELECT count(*) FROM comments WHERE beer_id = $1";
        char *main_query = "SELECT comment_id, comment_value, comment_author, s, sigma, lambda, is_private FROM comments WHERE beer_id = $1 OFFSET $2 LIMIT $3";
        const char *params[3];
        char str1[4096] = {0};
        snprintf(str1, 4096, "%d", beerID);
        params[0] = str1;

        char str2[4096] = {0};
        snprintf(str2, 4096, "%d", PAGE_SIZE * page);
        params[1] = str2;

        char str3[4096] = {0};
        snprintf(str3, 4096, "%d", PAGE_SIZE);
        params[2] = str3;
        main_res = PQexecParams(conn, main_query, 3, NULL, params, NULL, NULL, 0);
        if(PQresultStatus(main_res) != PGRES_TUPLES_OK) {

            return NULL;
        }
        count_res = PQexecParams(conn, count_query, 1, NULL, params, NULL, NULL, 0);
        if(PQresultStatus(count_res) != PGRES_TUPLES_OK) {

            return NULL;
        }

    }
    else {

        char *main_query = "SELECT comment_id, comment_value, comment_author, s, sigma, lambda, is_private FROM comments WHERE (beer_id = $1 AND (is_private = false OR comment_author = $2)) OFFSET $3 LIMIT $4";
        char *count_query = "SELECT count(*) FROM comments WHERE (beer_id = $1 AND (is_private = false OR comment_author = $2)) ";

        const char *params[4];

        char str1[4096] = {0};
        snprintf(str1, 4096, "%d", beerID);
        params[0] = str1;

        params[1] = requestingUser;
        char str2[4096] = {0};
        snprintf(str2, 4096, "%d", PAGE_SIZE * page);
        params[2] = str2;

        char str3[4096] = {0};
        snprintf(str3, 4096, "%d", PAGE_SIZE);
        params[3] = str3;

        main_res = PQexecParams(conn, main_query, 4, NULL, params, NULL, NULL, 0);
        if(PQresultStatus(main_res) != PGRES_TUPLES_OK) {

            return NULL;
        }
        count_res = PQexecParams(conn, count_query, 2, NULL, params, NULL, NULL, 0);
        if(PQresultStatus(count_res) != PGRES_TUPLES_OK) {

            return NULL;
        }

    }

    ListCommentsResponse *commentsResponse = calloc(1, sizeof(ListCommentsResponse));
    list_comments_response__init(commentsResponse);

    commentsResponse->pages_count = (atoi(PQgetvalue(count_res, 0, 0)) / PAGE_SIZE) + (atoi(PQgetvalue(count_res, 0, 0)) % PAGE_SIZE != 0);

    commentsResponse->current_page = page + 1;
    int nrows = PQntuples(main_res);

    Comment **comments = calloc(nrows, sizeof(Comment *));

    for (int i = 0; i < nrows; i++) {
        comments[i] = calloc(1, sizeof(Comment));
        comment__init(comments[i]);

        comments[i]->comment_id = atoi(PQgetvalue(main_res, i, 0));
        comments[i]->comment_value = strdup(PQgetvalue(main_res, i, 1));
        comments[i]->comment_author = strdup(PQgetvalue(main_res, i, 2));
        comments[i]->s = strdup(PQgetvalue(main_res, i, 3));
        comments[i]->sigma = strdup(PQgetvalue(main_res, i, 4));
        comments[i]->lambda = strdup(PQgetvalue(main_res, i, 5));

        comments[i]->is_private = strdup(PQgetvalue(main_res, i, 6));

    }
    commentsResponse->n_comments = nrows;
    commentsResponse->comments = comments;

    return commentsResponse;

}

  -(AddCommentResponse *)addComment: (const char *) comment_string beer_id : (uint32_t) beer_id owner: (const char *)owner is_private : (bool) is_private  s:(const char *)s sigma:(const char *)sigma lambda:(const char *)lambda {
        const char *query = "INSERT into comments(beer_id, comment_value, comment_author, is_private, s, sigma, lambda, timestamp) values ($1, $2, $3, $4, $5, $6, $7, now()) RETURNING comment_id";
        const char *params[7];
        char str[4096] = {0};
        snprintf(str, 4096, "%d", beer_id);

        char str1[4096] = {0};
        snprintf(str1, 4096, "%d", is_private);
        params[0] = str;
        params[1] = comment_string;
        params[2] = owner;
        params[3] = str1;
        params[4] = s;
        params[5] = sigma;
        params[6] = lambda;

        PGresult* res = PQexecParams(conn, query, 7, NULL, params, NULL, NULL, 0);
        if(PQresultStatus(res) != PGRES_TUPLES_OK) {

        return NULL;
        }
        char *entries_count = PQgetvalue(res, 0, 0);

    AddCommentResponse *out_resp = calloc(1, sizeof(AddCommentResponse));
    add_comment_response__init(out_resp);
    out_resp->comment_id = atoi(entries_count);
    return out_resp;
 }

@end

@interface UserSession:NSObject {
	User *_currentUser;
	Database *_database;

}
@end

@implementation UserSession
-(id)init {

	   self = [super init];
	   _currentUser = [[User alloc]init];
	   _database = [[Database alloc]init];
	   return self;
}

-(BOOL) validateCommandAccess: (int) command_id objectOwner: (char *)objectOwner {
    if (command_id >= ADD_BEER && command_id < ADD_PRIVATE_MESSAGE + 1) {
        if ([_currentUser->_userName isEqualToString:@""]) {
            return false;
        }
        return true;
    }

    if (command_id >= RESERVED2 && command_id < DELETE_COMMENT) {
        NSString *objectOwnerNS = [NSString stringWithCString:objectOwner encoding: 1];
        if ([_currentUser->_userName isEqualToString:objectOwnerNS]) {
            return true;
        }
        return false;
    }
    return true;

}
-(void) start {
    uint8_t *packet_buffer = calloc(1024 * 1024, sizeof(uint8_t));

    VerificationContext *verifCtx = [[VerificationContext alloc] init];
    while (1) {

        int data_sz = read(0, packet_buffer, 1024 * 1024);
        if (data_sz == 0 || data_sz == -1) {
            break;
        }

        Command *command = command__unpack(NULL, data_sz, packet_buffer);

        uint32_t command_id = command->commandid;
        if (verifCtx->exists && command_id != LOGIN_SEND_RESPONSE) {
            verifCtx->exists = false;
            mpz_set_str(verifCtx->sigma, "0", 10);
            mpz_set_str(verifCtx->e, "0", 10);
            mpz_set_str(verifCtx->gamma, "0", 10);
            mpz_set_str(verifCtx->alpha, "0", 10);
        }

        switch (command_id) {
        case REGISTER: {

            RegisterRequest *req = register_request__unpack(NULL, command->commandvalue.len, command->commandvalue.data);

            NSString *userNameToRegister = [NSString stringWithUTF8String:(req->nickname)];

            if ([_database userExists: req->nickname]) {

                Error error;
                error__init(&error);
                error.error_message = strdup("User already exists!");
                uint32_t packed_submsg_size = error__get_packed_size(&error);
                uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                error__pack(&error, send_submsg);

                Command commandToSend;
                command__init(&commandToSend);
                commandToSend.commandid = REGISTER;
                commandToSend.commandtype = ERROR;
                commandToSend.commandvalue.data = send_submsg;
                commandToSend.commandvalue.len = packed_submsg_size;

                uint32_t packed_size = command__get_packed_size(&commandToSend);

                uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                command__pack(&commandToSend, send_msg);
                write(1, &packed_size, 4);
                data_sz = write(1, send_msg, packed_size);
                break;

            }
            User *user = [User registerUser:userNameToRegister];

            if (user) {
                bool databaseRes = [_database registerUser:strdup([user->_userName UTF8String]) n:mpz_get_str(NULL,10,user->_group_n) gamma: mpz_get_str(NULL,10,user->_gamma) q: mpz_get_str(NULL,10,user->_q) alpha: mpz_get_str(NULL,10,user->_alpha)];
                if (databaseRes) {
                    RegisterResponse response;
                    register_response__init(&response);
                    response.nickname = strdup([user->_userName UTF8String]);
                    response.group_n = mpz_get_str(NULL,10,user->_group_n);
                    response.gamma = mpz_get_str(NULL,10,user->_gamma);
                    response.q = mpz_get_str(NULL,10,user->_q);
                    response.a = mpz_get_str(NULL,10,user->_a);
                    response.alpha = mpz_get_str(NULL,10,user->_alpha);
                    uint32_t packed_submsg_size = register_response__get_packed_size(&response);
                    uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                    register_response__pack(&response, send_submsg);

                    Command commandToSend;
                    command__init(&commandToSend);
                    commandToSend.commandid = REGISTER;
                    commandToSend.commandtype = RESPONSE;
                    commandToSend.commandvalue.data = send_submsg;
                    commandToSend.commandvalue.len = packed_submsg_size;

                    uint32_t packed_size = command__get_packed_size(&commandToSend);

                    uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                    command__pack(&commandToSend, send_msg);

                    write(1, &packed_size, 4);
                    data_sz = write(1, send_msg, packed_size);
                } else {
                    Error error;
                    error__init(&error);
                    error.error_message = strdup("Database interaction error!");
                    uint32_t packed_submsg_size = error__get_packed_size(&error);
                    uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                    error__pack(&error, send_submsg);

                    Command commandToSend;
                    command__init(&commandToSend);
                    commandToSend.commandid = REGISTER;
                    commandToSend.commandtype = ERROR;
                    commandToSend.commandvalue.data = send_submsg;
                    commandToSend.commandvalue.len = packed_submsg_size;

                    uint32_t packed_size = command__get_packed_size(&commandToSend);

                    uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                    command__pack(&commandToSend, send_msg);
                    write(1, &packed_size, 4);
                    data_sz = write(1, send_msg, packed_size);
                }

            } else {
                    Error error;
                    error__init(&error);
                    error.error_message = strdup("Database interation error!");
                    uint32_t packed_submsg_size = error__get_packed_size(&error);
                    uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                    error__pack(&error, send_submsg);

                    Command commandToSend;
                    command__init(&commandToSend);
                    commandToSend.commandid = REGISTER;
                    commandToSend.commandtype = ERROR;
                    commandToSend.commandvalue.data = send_submsg;
                    commandToSend.commandvalue.len = packed_submsg_size;

                    uint32_t packed_size = command__get_packed_size(&commandToSend);

                    uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                    command__pack(&commandToSend, send_msg);
                    write(1, &packed_size, 4);
                    data_sz = write(1, send_msg, packed_size);
            }
            break;
        case LOGIN_REQUEST_CHALLENGE: {

            LoginChallengeMsg1Request *loginChReq = login_challenge_msg1_request__unpack(NULL, command->commandvalue.len,  command->commandvalue.data);
            NSString *userNameToSignIn = [NSString stringWithUTF8String:(loginChReq->nickname)];

            GetUserDetailsResponse * userDetails = [_database getUserDetails:loginChReq->nickname page:1];
            if (userDetails) {

                mpz_t user_q;
                mpz_init(user_q);
                mpz_set_str(user_q, userDetails->q, 10);

                mpz_t e;
                mpz_init(e);
                [Cryptography generateRandomInRange:e paramBits:1024 paramCap:user_q];

                verifCtx->nickname = [userNameToSignIn copy];
                mpz_set_str(verifCtx->sigma, loginChReq->sigma, 10);
                mpz_init_set(verifCtx->e, e);
                mpz_set_str(verifCtx->gamma, userDetails->gamma, 10);
                mpz_set_str(verifCtx->alpha, userDetails->alpha, 10);
                mpz_set_str(verifCtx->group_n, userDetails->group_n, 10);
                mpz_set_str(verifCtx->q, userDetails->q, 10);
                verifCtx->exists = true;
                LoginChallengeMsg1Response challengeResponse;
                login_challenge_msg1_response__init(&challengeResponse);
                challengeResponse.e = mpz_get_str(NULL,10,e);

                uint32_t packed_submsg_size = login_challenge_msg1_response__get_packed_size(&challengeResponse);
                uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                login_challenge_msg1_response__pack(&challengeResponse, send_submsg);

                Command commandToSend;
                command__init(&commandToSend);
                commandToSend.commandid = LOGIN_REQUEST_CHALLENGE;
                commandToSend.commandtype = RESPONSE;
                commandToSend.commandvalue.data = send_submsg;
                commandToSend.commandvalue.len = packed_submsg_size;

                uint32_t packed_size = command__get_packed_size(&commandToSend);

                uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                command__pack(&commandToSend, send_msg);
                write(1, &packed_size, 4);
                data_sz = write(1, send_msg, packed_size);

            } else {
                    Error error;
                    error__init(&error);
                    error.error_message = strdup("User does not exist!");
                    uint32_t packed_submsg_size = error__get_packed_size(&error);
                    uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                    error__pack(&error, send_submsg);

                    Command commandToSend;
                    command__init(&commandToSend);
                    commandToSend.commandid = LOGIN_REQUEST_CHALLENGE;
                    commandToSend.commandtype = ERROR;
                    commandToSend.commandvalue.data = send_submsg;
                    commandToSend.commandvalue.len = packed_submsg_size;

                    uint32_t packed_size = command__get_packed_size(&commandToSend);

                    uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                    command__pack(&commandToSend, send_msg);
                    write(1, &packed_size, 4);
                    data_sz = write(1, send_msg, packed_size);
            }
            break;
        }
        }
        case LOGIN_SEND_RESPONSE:

            if (!verifCtx->exists) {

                break;
            }

            LoginChallengeMsg2Request *loginChAnswer = login_challenge_msg2_request__unpack(NULL, command->commandvalue.len,  command->commandvalue.data);

            mpz_t challenge_s;
            mpz_init(challenge_s);

            mpz_set_str(challenge_s, loginChAnswer->s, 10);

            mpz_t challenge_lambda;
            mpz_init(challenge_lambda);
            mpz_set_str(challenge_lambda, loginChAnswer->lambda, 10);

            mpz_t user_group_n;
            mpz_init(user_group_n);
            mpz_init_set(user_group_n, verifCtx->group_n);

            mpz_t power1;
            mpz_init(power1);
            mpz_powm(power1, verifCtx->gamma, challenge_s, user_group_n);

            mpz_t power2;
            mpz_init(power2);
            mpz_powm(power2, verifCtx->alpha, verifCtx->e, user_group_n);

            mpz_t power3;
            mpz_init(power3);
            mpz_powm(power3, challenge_lambda, verifCtx->q, user_group_n);

            mpz_t mul;
            mpz_init(mul);
            mpz_mul(mul, power1, power2);
            mpz_mod(mul, mul, user_group_n);
            mpz_mul(mul, mul, power3);
            mpz_mod(mul, mul, user_group_n);

            if(!mpz_cmp(mul, verifCtx->sigma)) {
                [_currentUser authenticateAs:verifCtx->nickname group_n : mpz_get_str(NULL,10,verifCtx->group_n) gamma: mpz_get_str(NULL,10,verifCtx->gamma) q: (char *) mpz_get_str(NULL,10,verifCtx->q) alpha: mpz_get_str(NULL,10,verifCtx->alpha)];

                LoginChallengeMsg2Response challengeMsg2Response;
                login_challenge_msg2_response__init(&challengeMsg2Response);
                challengeMsg2Response.nickname = strdup([verifCtx->nickname UTF8String]);
                uint32_t packed_size_1 = login_challenge_msg2_response__get_packed_size(&challengeMsg2Response);
                uint8_t *send_msg_1 = calloc(packed_size_1, sizeof(uint8_t));
                login_challenge_msg2_response__pack(&challengeMsg2Response, send_msg_1);

                Command commandToSend;
                command__init(&commandToSend);
                commandToSend.commandid = LOGIN_SEND_RESPONSE;
                commandToSend.commandtype = RESPONSE;
                commandToSend.commandvalue.data = send_msg_1;
                commandToSend.commandvalue.len = packed_size_1;

                uint32_t packed_size = command__get_packed_size(&commandToSend);

                uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                command__pack(&commandToSend, send_msg);
                write(1, &packed_size, 4);
                data_sz = write(1, send_msg, packed_size);

            }
            else {
                    Error error;
                    error__init(&error);
                    error.error_message = strdup("Authentication failed!");
                    uint32_t packed_submsg_size = error__get_packed_size(&error);
                    uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                    error__pack(&error, send_submsg);

                    Command commandToSend;
                    command__init(&commandToSend);
                    commandToSend.commandid = LOGIN_REQUEST_CHALLENGE;
                    commandToSend.commandtype = ERROR;
                    commandToSend.commandvalue.data = send_submsg;
                    commandToSend.commandvalue.len = packed_submsg_size;

                    uint32_t packed_size = command__get_packed_size(&commandToSend);

                    uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                    command__pack(&commandToSend, send_msg);
                    write(1, &packed_size, 4);

                    data_sz = write(1, send_msg, packed_size);
            }

            verifCtx->exists = false;
            mpz_set_str(verifCtx->sigma, "0", 10);
            mpz_set_str(verifCtx->e, "0", 10);
            mpz_set_str(verifCtx->gamma, "0", 10);
            mpz_set_str(verifCtx->alpha, "0", 10);
            mpz_set_str(verifCtx->group_n, "0", 10);

            break;
        case LIST_COMMENTS: {

            ListCommentsRequest *commentsRequest = list_comments_request__unpack(NULL, command->commandvalue.len,  command->commandvalue.data);

            uint32_t beer_id = commentsRequest->beer_id;
            uint32_t page = commentsRequest->page;

            char *beer_owner = [_database getBeerOwner:beer_id];

            if (beer_owner == NULL) {

                Error error;
                error__init(&error);
                error.error_message = strdup("Beer does not exist!");
                uint32_t packed_submsg_size = error__get_packed_size(&error);
                uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                error__pack(&error, send_submsg);

                Command commandToSend;
                command__init(&commandToSend);
                commandToSend.commandid = LIST_COMMENTS;
                commandToSend.commandtype = ERROR;
                commandToSend.commandvalue.data = send_submsg;
                commandToSend.commandvalue.len = packed_submsg_size;

                uint32_t packed_size = command__get_packed_size(&commandToSend);

                uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));
                command__pack(&commandToSend, send_msg);
                write(1, &packed_size, 4);
                data_sz = write(1, send_msg, packed_size);
                break;

            }

            NSString *ns_beer_owner = [NSString stringWithCString:beer_owner encoding:1];
            bool flag = [_currentUser->_userName isEqualToString:ns_beer_owner];
            ListCommentsResponse *comments = [_database getComments:beer_id page:page requestingUser:[_currentUser->_userName UTF8String] isOwner:flag];

            uint32_t packed_submsg_size =  list_comments_response__get_packed_size(comments);

            uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
            list_comments_response__pack(comments, send_submsg);

            Command commandToSend;
            command__init(&commandToSend);
            commandToSend.commandid = LIST_COMMENTS;
            commandToSend.commandtype = RESPONSE;
            commandToSend.commandvalue.data = send_submsg;
            commandToSend.commandvalue.len = packed_submsg_size;

            uint32_t packed_size = command__get_packed_size(&commandToSend);

            uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

            command__pack(&commandToSend, send_msg);

            write(1, &packed_size, 4);
            data_sz = write(1, send_msg, packed_size);

            break;
        }
        case GET_USER_INFO: {
            GetUserDetailsRequest *request = get_user_details_request__unpack(NULL, command->commandvalue.len, command->commandvalue.data);

            GetUserDetailsResponse *response = [_database getUserDetails:request->nickname page:request->page];
            if (response == NULL) {
                Error error;
                error__init(&error);
                error.error_message = strdup("User does not exist!");
                uint32_t packed_submsg_size = error__get_packed_size(&error);
                uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                error__pack(&error, send_submsg);

                Command commandToSend;
                command__init(&commandToSend);
                commandToSend.commandid = REGISTER;
                commandToSend.commandtype = ERROR;
                commandToSend.commandvalue.data = send_submsg;
                commandToSend.commandvalue.len = packed_submsg_size;

                uint32_t packed_size = command__get_packed_size(&commandToSend);

                uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                command__pack(&commandToSend, send_msg);
                write(1, &packed_size, 4);
                data_sz = write(1, send_msg, packed_size);
                break;
            }

            uint32_t packed_submsg_size =  get_user_details_response__get_packed_size(response);
            uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
            get_user_details_response__pack(response, send_submsg);

            Command commandToSend;
            command__init(&commandToSend);
            commandToSend.commandid = GET_USER_INFO;
            commandToSend.commandtype = RESPONSE;
            commandToSend.commandvalue.data = send_submsg;
            commandToSend.commandvalue.len = packed_submsg_size;

            uint32_t packed_size = command__get_packed_size(&commandToSend);

            uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

            command__pack(&commandToSend, send_msg);
            write(1, &packed_size, 4);
            data_sz = write(1, send_msg, packed_size);

            break;
        }

        case ADD_BEER: {
            if (![self validateCommandAccess:ADD_BEER objectOwner:""]) {
                Error error;
                error__init(&error);
                error.error_message = strdup("Unauthorized!");
                uint32_t packed_submsg_size = error__get_packed_size(&error);
                uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                error__pack(&error, send_submsg);

                Command commandToSend;
                command__init(&commandToSend);
                commandToSend.commandid = REGISTER;
                commandToSend.commandtype = ERROR;
                commandToSend.commandvalue.data = send_submsg;
                commandToSend.commandvalue.len = packed_submsg_size;

                uint32_t packed_size = command__get_packed_size(&commandToSend);

                uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                command__pack(&commandToSend, send_msg);
                write(1, &packed_size, 4);
                data_sz = write(1, send_msg, packed_size);
                break;
            }

            AddBeerRequest *request = add_beer_request__unpack(NULL, command->commandvalue.len, command->commandvalue.data);
            uint32_t new_id = [_database addBeer:strdup(request->beer_name) beerCreator:[_currentUser->_userName UTF8String]];
            if (new_id) {
                AddBeerResponse response;
                add_beer_response__init(&response);
                response.beer_id = new_id;
                uint32_t packed_submsg_size =  add_beer_response__get_packed_size(&response);
                uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                add_beer_response__pack(&response, send_submsg);

                Command commandToSend;
                command__init(&commandToSend);
                commandToSend.commandid = ADD_BEER;
                commandToSend.commandtype = RESPONSE;
                commandToSend.commandvalue.data = send_submsg;
                commandToSend.commandvalue.len = packed_submsg_size;

                uint32_t packed_size = command__get_packed_size(&commandToSend);

                uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                command__pack(&commandToSend, send_msg);
                write(1, &packed_size, 4);
                data_sz = write(1, send_msg, packed_size);
            }
            break;
        }

        case LIST_BEERS: {
            ListBeersRequest *request = list_beers_request__unpack(NULL, command->commandvalue.len, command->commandvalue.data);
            uint32_t page_number = request->page_number;
            page_number -= 1;
            ListBeersResponse *response = [_database listBeers:page_number];

            uint32_t packed_submsg_size =  list_beers_response__get_packed_size(response);
            uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
            list_beers_response__pack(response, send_submsg);

            Command commandToSend;
            command__init(&commandToSend);
            commandToSend.commandid = LIST_BEERS;
            commandToSend.commandtype = RESPONSE;
            commandToSend.commandvalue.data = send_submsg;
            commandToSend.commandvalue.len = packed_submsg_size;

            uint32_t packed_size = command__get_packed_size(&commandToSend);

            uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

            command__pack(&commandToSend, send_msg);
            write(1, &packed_size, 4);
            data_sz = write(1, send_msg, packed_size);
            break;
        }
        case ADD_COMMENT: {
            if (![self validateCommandAccess:ADD_COMMENT objectOwner:""]) {
                Error error;
                error__init(&error);
                error.error_message = strdup("Unauthorized!");
                uint32_t packed_submsg_size = error__get_packed_size(&error);
                uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                error__pack(&error, send_submsg);

                Command commandToSend;
                command__init(&commandToSend);
                commandToSend.commandid = REGISTER;
                commandToSend.commandtype = ERROR;
                commandToSend.commandvalue.data = send_submsg;
                commandToSend.commandvalue.len = packed_submsg_size;

                uint32_t packed_size = command__get_packed_size(&commandToSend);

                uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                command__pack(&commandToSend, send_msg);
                write(1, &packed_size, 4);
                data_sz = write(1, send_msg, packed_size);
                break;
            }

            AddCommentRequest *comment_request = add_comment_request__unpack(NULL, command->commandvalue.len, command->commandvalue.data);
            if (![_database doesBeerExist:comment_request->beer_id]) {
                Error error;
                error__init(&error);
                error.error_message = strdup("Beer does not exist!");
                uint32_t packed_submsg_size = error__get_packed_size(&error);
                uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                error__pack(&error, send_submsg);

                Command commandToSend;
                command__init(&commandToSend);
                commandToSend.commandid = REGISTER;
                commandToSend.commandtype = ERROR;
                commandToSend.commandvalue.data = send_submsg;
                commandToSend.commandvalue.len = packed_submsg_size;

                uint32_t packed_size = command__get_packed_size(&commandToSend);

                uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                command__pack(&commandToSend, send_msg);
                write(1, &packed_size, 4);
                data_sz = write(1, send_msg, packed_size);
            }

            mpz_t a;
            mpz_init(a);
            mpz_set_str(a, comment_request->private_key, 10);

            mpz_t s, sigma, lambda;
            mpz_init(s);
            mpz_init(sigma);
            mpz_init(lambda);
            NSString *message_to_sign = [NSString stringWithCString:comment_request->comment encoding:1];
            sign_message(message_to_sign, _currentUser->_group_n, _currentUser->_gamma, _currentUser->_q, _currentUser->_alpha, a, s, sigma, lambda);

            if (!verify_message(message_to_sign,  _currentUser->_group_n, _currentUser->_gamma, _currentUser->_q, _currentUser->_alpha, s, sigma, lambda)) {
                Error error;
                error__init(&error);
                error.error_message = strdup("Wrong private key specified!");
                uint32_t packed_submsg_size = error__get_packed_size(&error);
                uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                error__pack(&error, send_submsg);

                Command commandToSend;
                command__init(&commandToSend);
                commandToSend.commandid = REGISTER;
                commandToSend.commandtype = ERROR;
                commandToSend.commandvalue.data = send_submsg;
                commandToSend.commandvalue.len = packed_submsg_size;

                uint32_t packed_size = command__get_packed_size(&commandToSend);

                uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                command__pack(&commandToSend, send_msg);
                write(1, &packed_size, 4);
                data_sz = write(1, send_msg, packed_size);
            } else {

                AddCommentResponse *response = [_database addComment:comment_request->comment beer_id:comment_request->beer_id owner:[_currentUser->_userName UTF8String] is_private:comment_request->is_private s:mpz_get_str(NULL,10,s) sigma:mpz_get_str(NULL,10,sigma) lambda:mpz_get_str(NULL,10,lambda)];

                uint32_t packed_submsg_size =  add_comment_response__get_packed_size(response);
                uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                add_comment_response__pack(response, send_submsg);

                Command commandToSend;
                command__init(&commandToSend);
                commandToSend.commandid = ADD_COMMENT;
                commandToSend.commandtype = RESPONSE;
                commandToSend.commandvalue.data = send_submsg;
                commandToSend.commandvalue.len = packed_submsg_size;

                uint32_t packed_size = command__get_packed_size(&commandToSend);

                uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                command__pack(&commandToSend, send_msg);
                write(1, &packed_size, 4);
                data_sz = write(1, send_msg, packed_size);
            }
            break;

        }
        case DELETE_COMMENT: {

            DeleteCommentRequest *request = delete_comment_request__unpack(NULL, command->commandvalue.len, command->commandvalue.data);
            uint32_t comment_id = request->comment_id;
            char *comment_owner = [_database getCommentOwner:comment_id];

            if (![self validateCommandAccess:DELETE_COMMENT objectOwner:comment_owner]) {
                Error error;
                error__init(&error);
                error.error_message = strdup("Unauthorized!");
                uint32_t packed_submsg_size = error__get_packed_size(&error);
                uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                error__pack(&error, send_submsg);

                Command commandToSend;
                command__init(&commandToSend);
                commandToSend.commandid = REGISTER;
                commandToSend.commandtype = ERROR;
                commandToSend.commandvalue.data = send_submsg;
                commandToSend.commandvalue.len = packed_submsg_size;

                uint32_t packed_size = command__get_packed_size(&commandToSend);

                uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                command__pack(&commandToSend, send_msg);
                write(1, &packed_size, 4);
                data_sz = write(1, send_msg, packed_size);
                break;
            }

            bool result = [_database deleteComment:comment_id];
            if (result) {
                DeleteCommentResponse *response = calloc(1, sizeof(DeleteCommentResponse));
                delete_comment_response__init(response);
                response->success = true;

                uint32_t packed_submsg_size =  delete_comment_response__get_packed_size(response);
                uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                delete_comment_response__pack(response, send_submsg);

                Command commandToSend;
                command__init(&commandToSend);
                commandToSend.commandid = DELETE_COMMENT;
                commandToSend.commandtype = RESPONSE;
                commandToSend.commandvalue.data = send_submsg;
                commandToSend.commandvalue.len = packed_submsg_size;

                uint32_t packed_size = command__get_packed_size(&commandToSend);

                uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                command__pack(&commandToSend, send_msg);
                write(1, &packed_size, 4);
                data_sz = write(1, send_msg, packed_size);

            } else {
                Error error;
                error__init(&error);
                error.error_message = strdup("Error while deleting comment!");
                uint32_t packed_submsg_size = error__get_packed_size(&error);
                uint8_t *send_submsg = calloc(packed_submsg_size, sizeof(uint8_t));
                error__pack(&error, send_submsg);

                Command commandToSend;
                command__init(&commandToSend);
                commandToSend.commandid = DELETE_COMMENT;
                commandToSend.commandtype = ERROR;
                commandToSend.commandvalue.data = send_submsg;
                commandToSend.commandvalue.len = packed_submsg_size;

                uint32_t packed_size = command__get_packed_size(&commandToSend);

                uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));

                command__pack(&commandToSend, send_msg);
                write(1, &packed_size, 4);
                data_sz = write(1, send_msg, packed_size);
                break;
            }

            break;

        }

        }
        command__free_unpacked(command, NULL);

    }
    free(packet_buffer);
}

-( void) dealloc {

       [_currentUser release];
       [super dealloc];
}
@end

int main (int argc, const char * argv[])
{
    @autoreleasepool {
	    UserSession *session = [[UserSession alloc] init];
	    [session start];
    }

  return 0;
}
