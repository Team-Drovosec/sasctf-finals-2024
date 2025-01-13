#import <Foundation/Foundation.h>
#include "pr.pb-c.h"
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>
#include <gmp.h>

const char *beer = "               ______\n"
"              ( _ _ _)\n"
"               |_ _ |\n"
"              (_ _ _ )\n"
"               |    |\n"
"               |____|\n"
"               |/  \\|\n"
"               (2024)\n"
"               |\\__/|\n"
"               |    |\n"
"               |    |\n"
"              / .--. \\\n"
"           .-' :(..): `-.\n"
"       _.-'    `-..-'    `-._\n"
"     .'                      `.\n"
"     |___                  ___|\n"
"     |   `````--....--'''''   |\n"
"     |  |`````--....--'''''|  |\n"
"     |  |        $%#       |  |\n"
"     |  |        `'\"       |  |\n"
"     |  |  S E C U R I T Y |  |\n"
"     |  |   A N A L Y S T  |  |\n"
"     |  |    S U M M I T   |  |\n"
"     |  |                  |  |\n"
"     |  |        #-        |  |\n"
"     |  |       ###|       |  |\n"
"     |  |      .####.      |  |\n"
"     |  |      ######      |  |\n"
"     |  |      ######      |  |\n"
"     |  |        ##        |  |\n"
"     |  |  _____####_____  |  |\n"
"     |  |  __INDONESIA__   |  |\n"
"    .'  |                  |  `.\n"
"   (  `-.`````--....--'''''.-'  )\n"
"    ``-.._``--.._.._..:F_P:.--''\n"
"          ``--.._  _..--''\n"
"                 `'\n"
"                BALI            \n";

enum Commands {
	REGISTER,
	LOGIN_REQUEST_CHALLENGE,
	LOGIN_SEND_RESPONSE,
	DUMMY0,
	LIST_BEERS,
	DUMMY5,
	ADD_BEER,
	ADD_COMMENT,
	ADD_PRIVATE_MESSAGE,
	LIST_COMMENTS,
	DUMMY1,
	DUMMY2,
	DELETE_COMMENT,
	DUMMY3,
	GET_USERS,
    GET_USER_INFO
};

enum CommandType {

    REQUEST,
    RESPONSE,
    ERROR
};

void get_random_safe_number(mpz_t p, size_t bits) {
    FILE *f;
    if (bits < 3 || !(f = fopen("/dev/random", "rb"))) return ;
    size_t nbytes = (bits+7)>>3;
    uint8_t buf[nbytes];
    if (fread(buf, 1, nbytes, f) != nbytes) exit(1);
    mpz_import(p, nbytes, 1, 1, 0, 0, buf);

    fclose(f);
}

uint8_t *read_all(int socket, int length) {
    int read_length = 0;
    uint8_t *out_buf = calloc(length, sizeof(uint8_t));
    while (read_length < length) {
        read_length += recv(socket, out_buf + read_length, length - read_length, 0);
    }
    return out_buf;
}

void send_all(int socket, uint8_t *buf, int length) {
    int write_length = 0;
    while (write_length < length) {
        write_length += send(socket, buf + write_length, length - write_length, 0);
    }
    return;
}

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

int main (int argc, const char * argv[])
{

@autoreleasepool {
    uint8_t *packet_buffer = calloc(1024 * 1024, sizeof(uint8_t));
    int client_fd = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in serv_addr;
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(3000);
    if (inet_pton(AF_INET, "10.80.9.2", &serv_addr.sin_addr) <= 0) {
        printf("inet_pton error\n");
    }
    int status = connect(client_fd, (struct sockaddr*)&serv_addr, sizeof(serv_addr));
    char privKey [4096] = {0};
    mpz_t k;
    mpz_init(k);
    printf("%s\n", beer);
    printf("Welcome to BeerLogA - The logbook of voyagers exploring new beers!\n");
    while (1) {
    printf("Select command:\n");
    printf("[1]: Register\n");
    printf("[2]: Log in\n");
    printf("[3]: List available beers\n");
    printf("[4]: Add new beer (signed in users only)\n");
    printf("[5]: Add new comment (signed in users only)\n");
    printf("[6]: List available comments\n");
    printf("[7]: Delete a comment (signed in users only)\n");
    printf("[8]: Get information about user\n");
    int d;
    scanf("%d", &d);
    if (!(d >= 1 && d <= 8)) {
        printf("Wrong command choice!\n");
        continue;
    }

    int commandMapping [] = {-1, REGISTER, LOGIN_REQUEST_CHALLENGE, LIST_BEERS, ADD_BEER, ADD_COMMENT, LIST_COMMENTS, DELETE_COMMENT, GET_USER_INFO};
    d = commandMapping[d];
    Command commandToSend;
    command__init(&commandToSend);

    if (d == REGISTER) {
        commandToSend.commandid = REGISTER;
    	commandToSend.commandtype = REQUEST;
        RegisterRequest req;
        register_request__init(&req);
        char nickname [4096] = {0};
        printf ("Enter your nickname: \n");
        int nChars = scanf("%2048s", nickname);
        NSString *nicknameToRegister = [NSString stringWithCString:nickname encoding: 1];
        req.nickname = strdup([nicknameToRegister UTF8String]);
        uint32_t submsg_packed_size = register_request__get_packed_size(&req);
        uint8_t *send_submsg = calloc(submsg_packed_size, sizeof(uint8_t));
        register_request__pack(&req, send_submsg);

        commandToSend.commandvalue.data = send_submsg;
        commandToSend.commandvalue.len = submsg_packed_size;
        uint32_t packed_size = command__get_packed_size(&commandToSend);

        uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));
        command__pack(&commandToSend, send_msg);

        send(client_fd, &packed_size, 4, 0);
        send_all(client_fd, send_msg, packed_size);
        uint32_t bytes_received1 = 0;
        recv(client_fd, &bytes_received1, 4, 0);
        uint8_t *packet_buffer1 = read_all(client_fd, bytes_received1);

        Command *responseCommand = command__unpack(NULL, bytes_received1, packet_buffer1);
        if (responseCommand->commandtype == ERROR) {
            Error *error = error__unpack(NULL, responseCommand->commandvalue.len, responseCommand->commandvalue.data);
            printf("Error: %s\n", error->error_message);
            continue;
        }

        RegisterResponse *response = register_response__unpack(NULL, responseCommand->commandvalue.len, responseCommand->commandvalue.data);

        printf("Command result: \n");

        printf("Here is your public key:\n");
        printf("n = %s\n", response->group_n);
        printf("gamma = %s\n", response->gamma);
        printf("q = %s\n", response->q);
        printf("alpha = %s\n", response->alpha);
        printf("Here is your private key, remember to keep it a secret:\n");
        printf("a = %s\n", response->a);
    }

    if (d == LOGIN_REQUEST_CHALLENGE) {
        commandToSend.commandid = LOGIN_REQUEST_CHALLENGE;
    	commandToSend.commandtype = REQUEST;
        LoginChallengeMsg1Request loginChReq;
        login_challenge_msg1_request__init(&loginChReq);
        char nickname [4096] = {0};
        printf ("Enter your nickname: \n");
        scanf("%2048s", nickname);
        NSString *nicknameToLogin = [NSString stringWithCString:nickname encoding: 1];
        loginChReq.nickname = strdup([nicknameToLogin UTF8String]);

        printf ("Enter your private key: \n");
        scanf("%2048s", privKey);

        loginChReq.nickname = strdup([nicknameToLogin UTF8String]);

        Command commandToSend1;
        command__init(&commandToSend1);
        GetUserDetailsRequest userInfoRequest;
        get_user_details_request__init(&userInfoRequest);

        userInfoRequest.nickname = strdup(nickname);
        userInfoRequest.page = 1;
        uint32_t packed_size_submsg = get_user_details_request__get_packed_size(&userInfoRequest);
        uint8_t *send_submsg_ud = calloc(packed_size_submsg, sizeof(uint8_t));
        get_user_details_request__pack(&userInfoRequest, send_submsg_ud);

        commandToSend1.commandid = GET_USER_INFO;
    	commandToSend1.commandtype = REQUEST;
    	commandToSend1.commandvalue.data = send_submsg_ud;
        commandToSend1.commandvalue.len = packed_size_submsg;

        uint32_t packed_size_ud = command__get_packed_size(&commandToSend1);

        uint8_t *send_msg_ud = calloc(packed_size_ud, sizeof(uint8_t));
        command__pack(&commandToSend1, send_msg_ud);
        send(client_fd, &packed_size_ud, 4, 0);
        send_all(client_fd, send_msg_ud, packed_size_ud);

        uint32_t bytes_received1 = 0;
        recv(client_fd, &bytes_received1, 4, 0);
        uint8_t *packet_buffer1 = read_all(client_fd, bytes_received1);

       Command *responseCommand_ud = command__unpack(NULL, bytes_received1, packet_buffer1);

        if (responseCommand_ud->commandtype == ERROR) {
         Error *error = error__unpack(NULL, responseCommand_ud->commandvalue.len, responseCommand_ud->commandvalue.data);
            printf("Error: %s\n", error->error_message);
            continue;
       }

        GetUserDetailsResponse *response_ud = get_user_details_response__unpack(NULL, responseCommand_ud->commandvalue.len, responseCommand_ud->commandvalue.data);

        mpz_t user_group_n;
        mpz_init(user_group_n);
        mpz_set_str(user_group_n, response_ud->group_n, 10);
        mpz_t user_gamma;
        mpz_init(user_gamma);
        mpz_set_str(user_gamma,  response_ud->gamma, 10);
        mpz_t user_q;
        mpz_init(user_q);
        mpz_set_str(user_q,  response_ud->q, 10);
        mpz_t user_a;
        mpz_init(user_a);
        mpz_set_str(user_a, privKey, 10);
        mpz_t user_alpha;
        mpz_init(user_alpha);
        mpz_set_str(user_alpha,  response_ud->alpha, 10);
        [Cryptography generateRandomInRange:k paramBits:1024 paramCap:user_q];

        mpz_t sigma;
        mpz_init(sigma);
        mpz_powm(sigma, user_gamma, k, user_group_n);

        loginChReq.sigma = mpz_get_str(NULL,10,sigma);
        uint32_t submsg_packed_size = login_challenge_msg1_request__get_packed_size(&loginChReq);
        uint8_t *send_submsg = calloc(submsg_packed_size, sizeof(uint8_t));
        login_challenge_msg1_request__pack(&loginChReq, send_submsg);

        commandToSend.commandvalue.data = send_submsg;
        commandToSend.commandvalue.len = submsg_packed_size;
        uint32_t packed_size = command__get_packed_size(&commandToSend);

        uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));
        command__pack(&commandToSend, send_msg);
        send(client_fd, &packed_size, 4, 0);
        send_all(client_fd, send_msg, packed_size);
        bytes_received1 = 0;
        recv(client_fd, &bytes_received1, 4, 0);
        packet_buffer1 = read_all(client_fd, bytes_received1);

        Command *responseCommand_v = command__unpack(NULL, bytes_received1, packet_buffer1);
        if (responseCommand_v->commandtype == ERROR) {
            Error *error = error__unpack(NULL, responseCommand_v->commandvalue.len, responseCommand_v->commandvalue.data);
            printf("Error: %s\n", error->error_message);
            continue;
        }
        LoginChallengeMsg1Response *challengeResponse = login_challenge_msg1_response__unpack(NULL, responseCommand_v->commandvalue.len, responseCommand_v->commandvalue.data);

        mpz_t e;
        mpz_init(e);
        mpz_set_str(e, challengeResponse->e, 10);

        mpz_t product;
        mpz_init(product);
        mpz_mul(product, user_a, e);
        mpz_t x;
        mpz_init(x);
        mpz_sub(x, k, product);

        mpz_t s;
        mpz_init(s);

        mpz_t l;
        mpz_init(l);

        mpz_fdiv_qr(l, s, x, user_q);

        mpz_t lambda;
        mpz_init(lambda);
        mpz_powm(lambda, user_gamma, l, user_group_n);

        LoginChallengeMsg2Request challengeAnswers;
        login_challenge_msg2_request__init(&challengeAnswers);

        challengeAnswers.s = mpz_get_str(NULL,10,s);
        challengeAnswers.lambda = mpz_get_str(NULL,10,lambda);

        uint32_t submsg_packed_size2 = login_challenge_msg2_request__get_packed_size(&challengeAnswers);
        uint8_t *send_submsg2 = calloc(submsg_packed_size2, sizeof(uint8_t));
        login_challenge_msg2_request__pack(&challengeAnswers, send_submsg2);

        commandToSend.commandid = LOGIN_SEND_RESPONSE;
    	commandToSend.commandtype = REQUEST;
        commandToSend.commandvalue.data = send_submsg2;
        commandToSend.commandvalue.len = submsg_packed_size2;
        uint32_t packed_size2 = command__get_packed_size(&commandToSend);

        uint8_t *send_msg2 = calloc(packed_size2, sizeof(uint8_t));
        command__pack(&commandToSend, send_msg2);
        send(client_fd, &packed_size2, 4, 0);
        send_all(client_fd, send_msg2, packed_size2);
        bytes_received1 = 0;
        recv(client_fd, &bytes_received1, 4, 0);
        packet_buffer1 = read_all(client_fd, bytes_received1);

        Command *responseCommand = command__unpack(NULL, bytes_received1, packet_buffer1);

        if (responseCommand->commandtype == ERROR) {
            Error *error = error__unpack(NULL, responseCommand->commandvalue.len, responseCommand->commandvalue.data);
            printf("Error: %s\n", error->error_message);
            continue;
        }

        LoginChallengeMsg2Response *comment_response = login_challenge_msg2_response__unpack(NULL, responseCommand->commandvalue.len, responseCommand->commandvalue.data);
        printf("Authenticated as %s\n", comment_response->nickname);

    }

     if (d == LIST_COMMENTS) {
        ListCommentsRequest commentsRequest;
        list_comments_request__init(&commentsRequest);
        printf("Select beer id: \n");
        uint32_t beer_id;
        scanf("%d", &beer_id);
        uint32_t page;
        printf("Select page: \n");
        scanf("%d", &page);
        commentsRequest.beer_id = beer_id;
        commentsRequest.page = page;

        uint32_t packed_size_submsg = list_comments_request__get_packed_size(&commentsRequest);
        uint8_t *send_submsg = calloc(packed_size_submsg, sizeof(uint8_t));
        list_comments_request__pack(&commentsRequest, send_submsg);
        commandToSend.commandid = LIST_COMMENTS;
    	commandToSend.commandtype = REQUEST;
    	commandToSend.commandvalue.data = send_submsg;
        commandToSend.commandvalue.len = packed_size_submsg;

        uint32_t packed_size = command__get_packed_size(&commandToSend);

        uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));
        command__pack(&commandToSend, send_msg);

        send(client_fd, &packed_size, 4, 0);
        send_all(client_fd, send_msg, packed_size);

        uint32_t bytes_received1 = 0;
        recv(client_fd, &bytes_received1, 4, 0);
        uint8_t *packet_buffer1 = read_all(client_fd, bytes_received1);

        Command *responseCommand = command__unpack(NULL, bytes_received1, packet_buffer1);

        if (responseCommand->commandtype == ERROR) {
            Error *error = error__unpack(NULL, responseCommand->commandvalue.len, responseCommand->commandvalue.data);
            printf("Error: %s\n", error->error_message);
            continue;
        }

        ListCommentsResponse *response = list_comments_response__unpack(NULL, responseCommand->commandvalue.len, responseCommand->commandvalue.data);

        printf("Available comments for beer %d: page %d/%d\n", beer_id, response->current_page, response->pages_count);
        if (response->pages_count == 0 || response->current_page > response->pages_count) {
            printf("No comments available!\n");
            continue;
        }

        for (int i = 0; i < response->n_comments; i++) {
            printf("Comment ID %d: %s, by %s, signature (%s, %s, %s), private: %s\n", response->comments[i]->comment_id, response->comments[i]->comment_value, response->comments[i]->comment_author, response->comments[i]->s, response->comments[i]->sigma, response->comments[i]->lambda, response->comments[i]->is_private);
        }
    }

    if (d == GET_USER_INFO) {

        GetUserDetailsRequest userInfoRequest;
        get_user_details_request__init(&userInfoRequest);

        char nickname [4096] = {0};
        printf("Enter user nickname: \n");
        scanf("%2048s", nickname);

        userInfoRequest.nickname = strdup(nickname);

        printf("Enter page: \n");
        int page_num;
        scanf("%d", &page_num);
        userInfoRequest.page = page_num;
        uint32_t packed_size_submsg = get_user_details_request__get_packed_size(&userInfoRequest);
        uint8_t *send_submsg = calloc(packed_size_submsg, sizeof(uint8_t));
        get_user_details_request__pack(&userInfoRequest, send_submsg);

        commandToSend.commandid = GET_USER_INFO;
    	commandToSend.commandtype = REQUEST;
    	commandToSend.commandvalue.data = send_submsg;
        commandToSend.commandvalue.len = packed_size_submsg;

        uint32_t packed_size = command__get_packed_size(&commandToSend);

        uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));
        command__pack(&commandToSend, send_msg);
        send(client_fd, &packed_size, 4, 0);
        send_all(client_fd, send_msg, packed_size);

        uint32_t bytes_received1 = 0;
        recv(client_fd, &bytes_received1, 4, 0);
        uint8_t *packet_buffer1 = read_all(client_fd, bytes_received1);

        Command *responseCommand = command__unpack(NULL, bytes_received1, packet_buffer1);

        if (responseCommand->commandtype == ERROR) {
            Error *error = error__unpack(NULL, responseCommand->commandvalue.len, responseCommand->commandvalue.data);
            printf("Error: %s\n", error->error_message);
            continue;
        }

        GetUserDetailsResponse *response = get_user_details_response__unpack(NULL, responseCommand->commandvalue.len, responseCommand->commandvalue.data);
        printf("User information: %s\n", response->nickname);
        printf("Public Key: (%s %s %s %s)\n", response->group_n, response->gamma, response->q, response->alpha);
        printf("Public comments of user (page %d/%d)\n", response->current_page, response->pages_count);
        for (int i = 0; i < response->n_comments; i++) {
            printf("Comment ID %d: %s, beer %d, signature (%s, %s, %s)\n", response->comments[i]->comment_id, response->comments[i]->comment_value, response->comments[i]->beer_id, response->comments[i]->s,  response->comments[i]->sigma, response->comments[i]->lambda);
        }
    }

    if (d == ADD_BEER) {

        AddBeerRequest addBeerRequest;
        add_beer_request__init(&addBeerRequest);

        char beerName [4096] = {0};
        printf("Enter beer name: \n");
        scanf("%2048s", beerName);

        addBeerRequest.beer_name = strdup(beerName);

        uint32_t packed_size_submsg = add_beer_request__get_packed_size(&addBeerRequest);
        uint8_t *send_submsg = calloc(packed_size_submsg, sizeof(uint8_t));
        add_beer_request__pack(&addBeerRequest, send_submsg);

        commandToSend.commandid = ADD_BEER;
    	commandToSend.commandtype = REQUEST;
    	commandToSend.commandvalue.data = send_submsg;
        commandToSend.commandvalue.len = packed_size_submsg;

        uint32_t packed_size = command__get_packed_size(&commandToSend);

        uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));
        command__pack(&commandToSend, send_msg);
        send(client_fd, &packed_size, 4, 0);
        send_all(client_fd, send_msg, packed_size);
        uint32_t bytes_received1 = 0;
        recv(client_fd, &bytes_received1, 4, 0);
        uint8_t *packet_buffer1 = read_all(client_fd, bytes_received1);

        Command *responseCommand = command__unpack(NULL, bytes_received1, packet_buffer1);

        if (responseCommand->commandtype == ERROR) {
            Error *error = error__unpack(NULL, responseCommand->commandvalue.len, responseCommand->commandvalue.data);
            printf("Error: %s\n", error->error_message);
            continue;
        }
        AddBeerResponse *response = add_beer_response__unpack(NULL, responseCommand->commandvalue.len, responseCommand->commandvalue.data);
        printf("Created beer with ID: %d\n", response->beer_id);

    }

    if (d == LIST_BEERS) {

        ListBeersRequest listBeersRequest;
        list_beers_request__init(&listBeersRequest);

        int page_number;
        printf("Enter page number: \n");
        scanf("%d", &page_number);

        listBeersRequest.page_number = page_number;

        uint32_t packed_size_submsg = list_beers_request__get_packed_size(&listBeersRequest);
        uint8_t *send_submsg = calloc(packed_size_submsg, sizeof(uint8_t));
        list_beers_request__pack(&listBeersRequest, send_submsg);

        commandToSend.commandid = LIST_BEERS;
    	commandToSend.commandtype = REQUEST;
    	commandToSend.commandvalue.data = send_submsg;
        commandToSend.commandvalue.len = packed_size_submsg;

        uint32_t packed_size = command__get_packed_size(&commandToSend);

        uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));
        command__pack(&commandToSend, send_msg);
        send(client_fd, &packed_size, 4, 0);
        send_all(client_fd, send_msg, packed_size);
        uint32_t bytes_received1 = 0;
        recv(client_fd, &bytes_received1, 4, 0);
        uint8_t *packet_buffer1 = read_all(client_fd, bytes_received1);

        Command *responseCommand = command__unpack(NULL, bytes_received1, packet_buffer1);

        ListBeersResponse *response = list_beers_response__unpack(NULL, responseCommand->commandvalue.len, responseCommand->commandvalue.data);

        printf("Available beers: page %d/%d\n", response->page_number, response->number_pages);

        if (response->number_pages == 0 || response->page_number > response->number_pages) {
            printf("No beers available!\n");
            continue;
        }
        for (int i = 0; i < response->n_beers; i++) {
            printf("Beer ID %d: %s, brewed by %s\n", response->beers[i]->beer_id, response->beers[i]->beer_name, response->beers[i]->beer_creator);
        }

    }

    if (d == ADD_COMMENT) {
        char comment[4096];
        int beer_id;

        printf("Enter beer ID: \n");
        scanf("%d", &beer_id);
        printf("Read beer id %d\n", beer_id);
        printf("Enter comment text: \n");
        scanf("%2048s", comment);
        scanf("%2048[0-9a-zA-Z ]", comment);

        printf("Is this a private comment to the beer brewer? (Y/N)\n");
        char option;
        scanf("%c", &option);
        scanf("%c", &option);
        printf("%d\n", option);
        if (option != 'Y' && option != 'N') {
            printf("Wrong input format: not Y/N\n");

        } else {
            bool is_private = (option == 'Y');
            AddCommentRequest comment_request;
            add_comment_request__init(&comment_request);
            comment_request.beer_id = beer_id;
            comment_request.comment = comment;
            comment_request.private_key = privKey;
            comment_request.is_private = is_private;
            uint32_t packed_size_submsg = add_comment_request__get_packed_size(&comment_request);
            uint8_t *send_submsg = calloc(packed_size_submsg, sizeof(uint8_t));
            add_comment_request__pack(&comment_request, send_submsg);
            commandToSend.commandid = ADD_COMMENT;
        	commandToSend.commandtype = REQUEST;
        	commandToSend.commandvalue.data = send_submsg;
            commandToSend.commandvalue.len = packed_size_submsg;

            uint32_t packed_size = command__get_packed_size(&commandToSend);

            uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));
            command__pack(&commandToSend, send_msg);
            send(client_fd, &packed_size, 4, 0);
            send_all(client_fd, send_msg, packed_size);
            uint32_t bytes_received1 = 0;
            recv(client_fd, &bytes_received1, 4, 0);
            uint8_t *packet_buffer1 = read_all(client_fd, bytes_received1);

            Command *responseCommand = command__unpack(NULL, bytes_received1, packet_buffer1);

            AddCommentResponse *comment_response = add_comment_response__unpack(NULL, responseCommand->commandvalue.len, responseCommand->commandvalue.data);
            printf("Added new comment with ID %d\n", comment_response->comment_id);
        }

    }

    if (d == DELETE_COMMENT) {
        printf("ID of comment to be deleted: \n");
        uint32_t comment_id;
        scanf("%d", &comment_id);
        DeleteCommentRequest comment_request;
        delete_comment_request__init(&comment_request);
        comment_request.comment_id = comment_id;
        uint32_t packed_size_submsg = delete_comment_request__get_packed_size(&comment_request);
        uint8_t *send_submsg = calloc(packed_size_submsg, sizeof(uint8_t));
        delete_comment_request__pack(&comment_request, send_submsg);
        commandToSend.commandid = DELETE_COMMENT;
        commandToSend.commandtype = REQUEST;
        commandToSend.commandvalue.data = send_submsg;
        commandToSend.commandvalue.len = packed_size_submsg;

        uint32_t packed_size = command__get_packed_size(&commandToSend);

        uint8_t *send_msg = calloc(packed_size, sizeof(uint8_t));
        command__pack(&commandToSend, send_msg);
        send(client_fd, &packed_size, 4, 0);
        send_all(client_fd, send_msg, packed_size);
        uint32_t bytes_received1 = 0;
        recv(client_fd, &bytes_received1, 4, 0);
        uint8_t *packet_buffer1 = read_all(client_fd, bytes_received1);

        Command *responseCommand = command__unpack(NULL, bytes_received1, packet_buffer1);

        if (responseCommand->commandtype == ERROR) {
            Error *error = error__unpack(NULL, responseCommand->commandvalue.len, responseCommand->commandvalue.data);
            printf("Error: %s\n", error->error_message);
            continue;
        }
        DeleteCommentResponse *comment_response = delete_comment_response__unpack(NULL, responseCommand->commandvalue.len, responseCommand->commandvalue.data);
        printf("Comment deleted successfully\n", comment_response->success);
    }

    }

    close(client_fd);
}

}
