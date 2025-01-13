#include <Python.h>
#include <unistd.h>
#include <stdbool.h>
#include <libavformat/avformat.h>
#include <libavcodec/avcodec.h>
#include <libavfilter/avfilter.h>
#include <libavfilter/buffersink.h>
#include <libavfilter/buffersrc.h>
#include <libavutil/opt.h>

bool file_exist(char* filename) {
    return access(filename, F_OK) == 0;
}

static enum AVSampleFormat select_sample_format(const enum AVSampleFormat *fmts) {
    const enum AVSampleFormat *p;
    for (p = fmts; *p != AV_SAMPLE_FMT_NONE; p++) {
        if (*p == AV_SAMPLE_FMT_S16P || *p == AV_SAMPLE_FMT_FLTP) {
            return *p;
        }
    }
    return fmts[0];
}

int initialize_input(const char *input_file, AVFormatContext **fmt_ctx, AVCodecContext **dec_ctx, int *audio_stream_index) {
    if (avformat_open_input(fmt_ctx, input_file, NULL, NULL) < 0) {
        PyErr_SetString(PyExc_Exception, "Cannot open input file");
        return -1;
    }

    if (avformat_find_stream_info(*fmt_ctx, NULL) < 0) {
        PyErr_SetString(PyExc_Exception, "Cannot find stream information");
        return -1;
    }

    for (unsigned int i = 0; i < (*fmt_ctx)->nb_streams; i++) {
        if ((*fmt_ctx)->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_AUDIO) {
            *audio_stream_index = i;
            break;
        }
    }

    if (*audio_stream_index == -1) {
        PyErr_SetString(PyExc_Exception, "Cannot find audio stream in the input file");
        return -1;
    }

    AVStream *audio_stream = (*fmt_ctx)->streams[*audio_stream_index];
    AVCodec *dec = avcodec_find_decoder(audio_stream->codecpar->codec_id);
    if (!dec) {
        PyErr_SetString(PyExc_Exception, "Failed to find decoder for the audio stream");
        return -1;
    }

    *dec_ctx = avcodec_alloc_context3(dec);
    if (!*dec_ctx) {
        PyErr_SetString(PyExc_Exception, "Failed to allocate the decoder context");
        return -1;
    }

    if (avcodec_parameters_to_context(*dec_ctx, audio_stream->codecpar) < 0) {
        PyErr_SetString(PyExc_Exception, "Failed to copy decoder parameters to input decoder context");
        return -1;
    }

    if (avcodec_open2(*dec_ctx, dec, NULL) < 0) {
        PyErr_SetString(PyExc_Exception, "Failed to open decoder");
        return -1;
    }

    return 0;
}

int initialize_output(const char *output_file, AVFormatContext **out_fmt_ctx, AVCodecContext **enc_ctx,
                      AVCodecContext *dec_ctx, AVStream **out_stream, AVFormatContext *fmt_ctx, AVStream *audio_stream) {
    AVCodec *encoder = avcodec_find_encoder(AV_CODEC_ID_MP3);
    if (!encoder) {
        PyErr_SetString(PyExc_Exception, "Necessary encoder not found");
        return -1;
    }

    *enc_ctx = avcodec_alloc_context3(encoder);
    if (!*enc_ctx) {
        PyErr_SetString(PyExc_Exception, "Failed to allocate the encoder context");
        return -1;
    }

    (*enc_ctx)->bit_rate = 192000;
    (*enc_ctx)->sample_rate = dec_ctx->sample_rate;

    if (encoder->supported_samplerates) {
        const int *p = encoder->supported_samplerates;
        int best_rate = 0;
        while (*p) {
            if (*p == dec_ctx->sample_rate) {
                best_rate = dec_ctx->sample_rate;
                break;
            }
            p++;
        }
        if (best_rate == 0) {
            (*enc_ctx)->sample_rate = encoder->supported_samplerates[0];
        }
    }

    (*enc_ctx)->channel_layout = dec_ctx->channel_layout ? dec_ctx->channel_layout : AV_CH_LAYOUT_STEREO;
    if (encoder->channel_layouts) {
        const uint64_t *p = encoder->channel_layouts;
        uint64_t best_ch_layout = 0;
        while (*p) {
            if (*p == (*enc_ctx)->channel_layout) {
                best_ch_layout = (*enc_ctx)->channel_layout;
                break;
            }
            p++;
        }
        if (best_ch_layout == 0) {
            (*enc_ctx)->channel_layout = encoder->channel_layouts[0];
        }
    }

    (*enc_ctx)->channels = av_get_channel_layout_nb_channels((*enc_ctx)->channel_layout);
    (*enc_ctx)->sample_fmt = select_sample_format(encoder->sample_fmts);
    (*enc_ctx)->time_base = (AVRational){1, (*enc_ctx)->sample_rate};

    if (avformat_alloc_output_context2(out_fmt_ctx, NULL, NULL, output_file) < 0) {
        PyErr_SetString(PyExc_Exception, "Could not create output context");
        return -1;
    }

    av_dict_copy(&(*out_fmt_ctx)->metadata, fmt_ctx->metadata, 0);

    if ((*out_fmt_ctx)->oformat->flags & AVFMT_GLOBALHEADER)
        (*enc_ctx)->flags |= AV_CODEC_FLAG_GLOBAL_HEADER;

    if (avcodec_open2(*enc_ctx, encoder, NULL) < 0) {
        PyErr_SetString(PyExc_Exception, "Cannot open audio encoder");
        return -1;
    }

    *out_stream = avformat_new_stream(*out_fmt_ctx, NULL);
    if (!*out_stream) {
        PyErr_SetString(PyExc_Exception, "Failed to allocate output stream");
        return -1;
    }

    if (avcodec_parameters_from_context((*out_stream)->codecpar, *enc_ctx) < 0) {
        PyErr_SetString(PyExc_Exception, "Failed to copy encoder parameters to output stream");
        return -1;
    }

    (*out_stream)->time_base = (*enc_ctx)->time_base;

    av_dict_copy(&(*out_stream)->metadata, audio_stream->metadata, 0);

    if (!((*out_fmt_ctx)->oformat->flags & AVFMT_NOFILE)) {
        if (avio_open(&(*out_fmt_ctx)->pb, output_file, AVIO_FLAG_WRITE) < 0) {
            PyErr_SetString(PyExc_Exception, "Could not open output file");
            return -1;
        }
    }

    if (avformat_write_header(*out_fmt_ctx, NULL) < 0) {
        PyErr_SetString(PyExc_Exception, "Error occurred when opening output file");
        return -1;
    }

    return 0;
}

int initialize_filters(const char *filter_descr, AVFilterGraph **filter_graph, AVFilterContext **buffersrc_ctx, AVFilterContext **buffersink_ctx, AVCodecContext *dec_ctx, AVCodecContext *enc_ctx, AVStream *audio_stream) {
    char args[512];
    int ret = 0;

    *filter_graph = avfilter_graph_alloc();
    if (!*filter_graph) {
        PyErr_SetString(PyExc_Exception, "Failed to allocate filter graph");
        return -1;
    }

    snprintf(args, sizeof(args),
             "time_base=%d/%d:sample_rate=%d:sample_fmt=%s:channel_layout=0x%"PRIx64,
             audio_stream->time_base.num, audio_stream->time_base.den, dec_ctx->sample_rate,
             av_get_sample_fmt_name(dec_ctx->sample_fmt), dec_ctx->channel_layout);

    ret = avfilter_graph_create_filter(buffersrc_ctx, avfilter_get_by_name("abuffer"), "in",
                                       args, NULL, *filter_graph);
    if (ret < 0) {
        PyErr_SetString(PyExc_Exception, "Cannot create buffer source");
        return -1;
    }

    ret = avfilter_graph_create_filter(buffersink_ctx, avfilter_get_by_name("abuffersink"), "out",
                                       NULL, NULL, *filter_graph);
    if (ret < 0) {
        PyErr_SetString(PyExc_Exception, "Cannot create buffer sink");
        return -1;
    }

    ret = av_opt_set_bin(*buffersink_ctx, "sample_fmts",
                         (uint8_t *)&enc_ctx->sample_fmt, sizeof(enc_ctx->sample_fmt),
                         AV_OPT_SEARCH_CHILDREN);
    if (ret < 0) {
        PyErr_SetString(PyExc_Exception, "Cannot set output sample format for filter graph");
        return -1;
    }

    ret = av_opt_set_bin(*buffersink_ctx, "channel_layouts",
                         (uint8_t *)&enc_ctx->channel_layout, sizeof(enc_ctx->channel_layout),
                         AV_OPT_SEARCH_CHILDREN);
    if (ret < 0) {
        PyErr_SetString(PyExc_Exception, "Cannot set output channel layout for filter graph");
        return -1;
    }

    ret = av_opt_set_bin(*buffersink_ctx, "sample_rates",
                         (uint8_t *)&enc_ctx->sample_rate, sizeof(enc_ctx->sample_rate),
                         AV_OPT_SEARCH_CHILDREN);
    if (ret < 0) {
        PyErr_SetString(PyExc_Exception, "Cannot set output sample rate for filter graph");
        return -1;
    }

    AVFilterInOut *inputs = avfilter_inout_alloc();
    AVFilterInOut *outputs = avfilter_inout_alloc();

    if (!inputs || !outputs) {
        PyErr_SetString(PyExc_Exception, "Cannot allocate filter inputs/outputs");
        return -1;
    }

    outputs->name = av_strdup("in");
    outputs->filter_ctx = *buffersrc_ctx;
    outputs->pad_idx = 0;
    outputs->next = NULL;

    inputs->name = av_strdup("out");
    inputs->filter_ctx = *buffersink_ctx;
    inputs->pad_idx = 0;
    inputs->next = NULL;

    char full_filter_descr[1024];
    snprintf(full_filter_descr, sizeof(full_filter_descr),
             "%s, asetnsamples=n=%d:p=1", filter_descr, enc_ctx->frame_size);

    ret = avfilter_graph_parse_ptr(*filter_graph, full_filter_descr, &inputs, &outputs, NULL);
    if (ret < 0) {
        PyErr_SetString(PyExc_Exception, "Error while parsing the filter graph");
        avfilter_inout_free(&inputs);
        avfilter_inout_free(&outputs);
        return -1;
    }

    ret = avfilter_graph_config(*filter_graph, NULL);
    if (ret < 0) {
        PyErr_SetString(PyExc_Exception, "Error while configuring the filter graph");
        avfilter_inout_free(&inputs);
        avfilter_inout_free(&outputs);
        return -1;
    }

    avfilter_inout_free(&inputs);
    avfilter_inout_free(&outputs);

    return 0;
}

int process_audio(AVFormatContext *fmt_ctx, AVFormatContext *out_fmt_ctx, AVCodecContext *dec_ctx, AVCodecContext *enc_ctx, AVFilterGraph *filter_graph, AVFilterContext *buffersrc_ctx, AVFilterContext *buffersink_ctx, int audio_stream_index, AVStream *out_stream) {
    AVPacket packet;
    AVFrame *frame = av_frame_alloc(), *filt_frame = av_frame_alloc();
    int ret;

    while (1) {
        ret = av_read_frame(fmt_ctx, &packet);
        if (ret < 0)
            break;

        if (packet.stream_index == audio_stream_index) {
            ret = avcodec_send_packet(dec_ctx, &packet);
            av_packet_unref(&packet);
            if (ret < 0) {
                PyErr_SetString(PyExc_Exception, "Error while sending a packet to the decoder");
                av_frame_free(&frame);
                av_frame_free(&filt_frame);
                return -1;
            }

            while ((ret = avcodec_receive_frame(dec_ctx, frame)) >= 0) {
                frame->pts = frame->best_effort_timestamp;

                ret = av_buffersrc_add_frame(buffersrc_ctx, frame);
                if (ret < 0) {
                    PyErr_SetString(PyExc_Exception, "Error while feeding the audio filtergraph");
                    av_frame_free(&frame);
                    av_frame_free(&filt_frame);
                    return -1;
                }

                while ((ret = av_buffersink_get_frame(buffersink_ctx, filt_frame)) >= 0) {
                    filt_frame->pts = av_rescale_q(filt_frame->pts, buffersink_ctx->inputs[0]->time_base, enc_ctx->time_base);

                    ret = avcodec_send_frame(enc_ctx, filt_frame);
                    if (ret < 0) {
                        PyErr_SetString(PyExc_Exception, "Error while sending a frame to the encoder");
                        av_frame_free(&frame);
                        av_frame_free(&filt_frame);
                        return -1;
                    }

                    while ((ret = avcodec_receive_packet(enc_ctx, &packet)) >= 0) {
                        packet.stream_index = out_stream->index;
                        av_packet_rescale_ts(&packet, enc_ctx->time_base, out_stream->time_base);

                        ret = av_interleaved_write_frame(out_fmt_ctx, &packet);
                        if (ret < 0) {
                            PyErr_SetString(PyExc_Exception, "Error while writing a packet to the output file");
                            av_packet_unref(&packet);
                            av_frame_free(&frame);
                            av_frame_free(&filt_frame);
                            return -1;
                        }
                        av_packet_unref(&packet);
                    }

                    av_frame_unref(filt_frame);
                }

                av_frame_unref(frame);
            }

            if (ret == AVERROR_EOF || ret == AVERROR(EAGAIN)) {
            } else if (ret < 0) {
                PyErr_SetString(PyExc_Exception, "Error during decoding");
                av_frame_free(&frame);
                av_frame_free(&filt_frame);
                return -1;
            }
        } else {
            av_packet_unref(&packet);
        }
    }

    ret = avcodec_send_packet(dec_ctx, NULL);
    while ((ret = avcodec_receive_frame(dec_ctx, frame)) >= 0) {
        frame->pts = frame->best_effort_timestamp;

        ret = av_buffersrc_add_frame(buffersrc_ctx, frame);
        if (ret < 0) {
            PyErr_SetString(PyExc_Exception, "Error while feeding the audio filtergraph");
            av_frame_free(&frame);
            av_frame_free(&filt_frame);
            return -1;
        }

        while ((ret = av_buffersink_get_frame(buffersink_ctx, filt_frame)) >= 0) {
            filt_frame->pts = av_rescale_q(filt_frame->pts, buffersink_ctx->inputs[0]->time_base, enc_ctx->time_base);

            ret = avcodec_send_frame(enc_ctx, filt_frame);
            if (ret < 0) {
                PyErr_SetString(PyExc_Exception, "Error while sending a frame to the encoder");
                av_frame_free(&frame);
                av_frame_free(&filt_frame);
                return -1;
            }

            while ((ret = avcodec_receive_packet(enc_ctx, &packet)) >= 0) {
                packet.stream_index = out_stream->index;
                av_packet_rescale_ts(&packet, enc_ctx->time_base, out_stream->time_base);

                ret = av_interleaved_write_frame(out_fmt_ctx, &packet);
                if (ret < 0) {
                    PyErr_SetString(PyExc_Exception, "Error while writing a packet to the output file");
                    av_packet_unref(&packet);
                    av_frame_free(&frame);
                    av_frame_free(&filt_frame);
                    return -1;
                }
                av_packet_unref(&packet);
            }

            av_frame_unref(filt_frame);
        }

        av_frame_unref(frame);
    }

    av_buffersrc_add_frame(buffersrc_ctx, NULL);
    while ((ret = av_buffersink_get_frame(buffersink_ctx, filt_frame)) >= 0) {
        filt_frame->pts = av_rescale_q(filt_frame->pts, buffersink_ctx->inputs[0]->time_base, enc_ctx->time_base);

        ret = avcodec_send_frame(enc_ctx, filt_frame);
        if (ret < 0) {
            PyErr_SetString(PyExc_Exception, "Error while sending a frame to the encoder");
            av_frame_free(&frame);
            av_frame_free(&filt_frame);
            return -1;
        }

        while ((ret = avcodec_receive_packet(enc_ctx, &packet)) >= 0) {
            packet.stream_index = out_stream->index;
            av_packet_rescale_ts(&packet, enc_ctx->time_base, out_stream->time_base);

            ret = av_interleaved_write_frame(out_fmt_ctx, &packet);
            if (ret < 0) {
                PyErr_SetString(PyExc_Exception, "Error while writing a packet to the output file");
                av_packet_unref(&packet);
                av_frame_free(&frame);
                av_frame_free(&filt_frame);
                return -1;
            }
            av_packet_unref(&packet);
        }

        av_frame_unref(filt_frame);
    }

    ret = avcodec_send_frame(enc_ctx, NULL);
    while ((ret = avcodec_receive_packet(enc_ctx, &packet)) >= 0) {
        packet.stream_index = out_stream->index;
        av_packet_rescale_ts(&packet, enc_ctx->time_base, out_stream->time_base);

        ret = av_interleaved_write_frame(out_fmt_ctx, &packet);
        if (ret < 0) {
            PyErr_SetString(PyExc_Exception, "Error while writing a packet to the output file");
            av_packet_unref(&packet);
            av_frame_free(&frame);
            av_frame_free(&filt_frame);
            return -1;
        }
        av_packet_unref(&packet);
    }

    av_frame_free(&frame);
    av_frame_free(&filt_frame);

    return 0;
}

static PyObject* applyFilter(char* input_file, char* output_file, char* filter_string) {
    if (!file_exist(input_file)) {
        PyErr_SetString(PyExc_FileNotFoundError, "Input file does not exist");
        return NULL;
    }

    AVFormatContext *fmt_ctx = NULL, *out_fmt_ctx = NULL;
    AVCodecContext *dec_ctx = NULL, *enc_ctx = NULL;
    AVFilterContext *buffersink_ctx = NULL, *buffersrc_ctx = NULL;
    AVFilterGraph *filter_graph = NULL;
    AVStream *audio_stream = NULL, *out_stream = NULL;
    int audio_stream_index = -1;
    int ret;

    ret = initialize_input(input_file, &fmt_ctx, &dec_ctx, &audio_stream_index);
    if (ret < 0) {
        return NULL;
    }

    audio_stream = fmt_ctx->streams[audio_stream_index];

    ret = initialize_output(output_file, &out_fmt_ctx, &enc_ctx, dec_ctx, &out_stream, fmt_ctx, audio_stream);
    if (ret < 0) {
        goto end;
    }

    char filter_descr[512];
    snprintf(filter_descr, sizeof(filter_descr),
             "%s aformat=sample_fmts=%s:channel_layouts=0x%"PRIx64, filter_string,
             av_get_sample_fmt_name(enc_ctx->sample_fmt), enc_ctx->channel_layout);

    ret = initialize_filters(filter_descr, &filter_graph, &buffersrc_ctx, &buffersink_ctx, dec_ctx, enc_ctx, audio_stream);
    if (ret < 0) {
        goto end;
    }

    ret = process_audio(fmt_ctx, out_fmt_ctx, dec_ctx, enc_ctx, filter_graph, buffersrc_ctx, buffersink_ctx, audio_stream_index, out_stream);
    if (ret < 0) {
        goto end;
    }

    av_write_trailer(out_fmt_ctx);

end:
    if (filter_graph)
        avfilter_graph_free(&filter_graph);
    if (dec_ctx)
        avcodec_free_context(&dec_ctx);
    if (enc_ctx)
        avcodec_free_context(&enc_ctx);
    if (fmt_ctx)
        avformat_close_input(&fmt_ctx);
    if (out_fmt_ctx && !(out_fmt_ctx->oformat->flags & AVFMT_NOFILE))
        avio_closep(&out_fmt_ctx->pb);
    if (out_fmt_ctx)
        avformat_free_context(out_fmt_ctx);

    if (ret < 0)
        return NULL;

    return Py_BuildValue("b", true);
}

void concat(const char *str1, const char *str2, char *ret, ssize_t ret_size) {
    snprintf(ret, ret_size, "%s%s", str1, str2);
}

void buildFilterString(char** coefs, char *res, ssize_t ret_size) {
    res[0] = '\0';

    if (strcmp(coefs[0], "0") != 0) {
        char temp[512];
        concat(res, "bass=g=%s, ", temp, sizeof(temp));
        snprintf(res, ret_size, temp, coefs[0]);
    }

    if (strcmp(coefs[1], "0") != 0) {
        char temp[512];
        concat(res, "volume=%s, ", temp, sizeof(temp));
        snprintf(res, ret_size, temp, coefs[1]);
    }

    if (strcmp(coefs[2], "0") != 0) {
        char temp[512];
        concat(res, "aecho=1.0:0.75:%s:0.5, ", temp, sizeof(temp));
        snprintf(res, ret_size, temp, coefs[2]);
    }

    if (strcmp(coefs[3], "0") != 0) {
        char temp[512];
        concat(res, "asetrate=48000*%s, ", temp, sizeof(temp));
        snprintf(res, ret_size, temp, coefs[3]);
    }

    if (strcmp(coefs[4], "0") != 0) {
        char temp[512];
        concat(res, "treble=g=%s, ", temp, sizeof(temp));
        snprintf(res, ret_size, temp, coefs[4]);
    }

    if (strcmp(coefs[5], "0") != 0) {
        char temp[512];
        concat(res, "loudnorm, ", temp, sizeof(temp));
        snprintf(res, ret_size, temp, "");
    }
}

static PyObject* bassboost_taz(PyObject* self, PyObject* args) {
    char *input_file = NULL, *output_file = NULL;
    if (!PyArg_ParseTuple(args, "ss", &input_file, &output_file)) {
        return NULL;
    }

    char filter_string[512];
    char* coefs[6] = {"10", "0", "0", "0", "0", "1"};
    buildFilterString(coefs, filter_string, 512);
    return applyFilter(input_file, output_file, filter_string);
}

static PyObject* bassboost_pacan(PyObject* self, PyObject* args) {
    char *input_file = NULL, *output_file = NULL;
    if (!PyArg_ParseTuple(args, "ss", &input_file, &output_file)) {
        return NULL;
    }

    char filter_string[512];
    char* coefs[6] = {"10", "0", "0", "0", "0", "0"};
    buildFilterString(coefs, filter_string, 512);
    return applyFilter(input_file, output_file, filter_string);
}

static PyObject* earrape(PyObject* self, PyObject* args) {
    char *input_file = NULL, *output_file = NULL;
    if (!PyArg_ParseTuple(args, "ss", &input_file, &output_file)) {
        return NULL;
    }

    char filter_string[512];
    char* coefs[6] = {"20", "12", "0", "0", "0", "0"};
    buildFilterString(coefs, filter_string, 512);
    return applyFilter(input_file, output_file, filter_string);
}

static PyObject* reverb(PyObject* self, PyObject* args) {
    char *input_file = NULL, *output_file = NULL;
    if (!PyArg_ParseTuple(args, "ss", &input_file, &output_file)) {
        return NULL;
    }

    char filter_string[512];
    char* coefs[6] = {"0", "0", "38", "0", "0", "0"};
    buildFilterString(coefs, filter_string, 512);
    return applyFilter(input_file, output_file, filter_string);
}

static PyObject* nightcore(PyObject* self, PyObject* args) {
    char *input_file = NULL, *output_file = NULL;
    if (!PyArg_ParseTuple(args, "ss", &input_file, &output_file)) {
        return NULL;
    }

    char filter_string[512];
    char* coefs[6] = {"2", "0", "0", "1.15", "0", "0"};
    buildFilterString(coefs, filter_string, 512);
    return applyFilter(input_file, output_file, filter_string);
}

static PyObject* daycore(PyObject* self, PyObject* args) {
    char *input_file = NULL, *output_file = NULL;
    if (!PyArg_ParseTuple(args, "ss", &input_file, &output_file)) {
        return NULL;
    }

    char filter_string[512];
    char* coefs[6] = {"0", "0", "45", "0.8", "0", "0"};
    buildFilterString(coefs, filter_string, 512);
    return applyFilter(input_file, output_file, filter_string);
}

static PyObject* custom(PyObject* self, PyObject* args) {
    char *input_file = NULL, *output_file = NULL;
    PyObject *coefs;
    if (!PyArg_ParseTuple(args, "ssO!", &input_file, &output_file, &PyList_Type, &coefs)) {
        return NULL;
    }

    Py_ssize_t list_size = PyList_Size(coefs);
    if (list_size != 6) {
        PyErr_SetString(PyExc_ValueError, "The list must contain exactly 6 elements");
        return NULL;
    }

    char *coefs_c[6];

    for (int i = 0; i < 6; i++) {
        PyObject *item = PyList_GetItem(coefs, i);
        if (PyUnicode_Check(item)) {
            const char *item_str = PyUnicode_AsUTF8(item);
            if (item_str == NULL) {
                PyErr_SetString(PyExc_ValueError, "Not a string");
                return NULL;
            }

            coefs_c[i] = strdup(item_str);
            if (coefs_c[i] == NULL) {
                for (int j = 0; j < i; j++) {
                    free(coefs_c[j]);
                }
                PyErr_SetString(PyExc_MemoryError, "Unable to allocate memory");
                return NULL;
            }
        } else {
            for (int j = 0; j < i; j++) {
                free(coefs_c[j]);
            }
            PyErr_SetString(PyExc_TypeError, "Not a string");
            return NULL;
        }
    }

    char filter_string[512];
    buildFilterString(coefs_c, filter_string, 512);

    return Py_BuildValue("b", applyFilter(input_file, output_file, filter_string));
}

static PyMethodDef DjMethods[] = {
    {"bassboost_taz", bassboost_taz, METH_VARARGS, "bass for taz"},
    {"bassboost_pacan", bassboost_pacan, METH_VARARGS, "bass for real men"},
    {"nightcore", nightcore, METH_VARARGS, "tomboy"},
    {"daycore", daycore, METH_VARARGS, "redan"},
    {"reverb", reverb, METH_VARARGS, "minecraft cave"},
    {"earrape", earrape, METH_VARARGS, "funnny discord"},
    {"custom", custom, METH_VARARGS, "custom remix"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef dj_module = {
    PyModuleDef_HEAD_INIT,
    "dj",
    NULL,
    -1,
    DjMethods
};

PyMODINIT_FUNC PyInit_dj(void) {
    return PyModule_Create(&dj_module);
}
