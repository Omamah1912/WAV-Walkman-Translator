#include <iostream>
#include <fstream>
#include <string>
#include <cmath>
#include <vector>
using namespace std;

const string chunk_id     = "RIFF";
const string format       = "WAVE";
const string subchunk1_id = "fmt ";
const int subchunk1_size  = 16;
const int audio_format    = 1;
const int num_channels    = 2;
const int sample_rate     = 44100;
const int bits_per_sample = 16;
const int byte_rate       = sample_rate * num_channels * bits_per_sample / 8;
const int block_align     = num_channels * bits_per_sample / 8;
const string subchunk2_id = "data";
const int max_amp         = 32760;

void write_as_bytes(ofstream& file, int val, int byte_size) {
    file.write(reinterpret_cast<const char*>(&val), byte_size);
}

int main() {
    // --- read notes from file: each line is "frequency duration" ---
    vector<double> notes, durations;
    ifstream in("notes.txt");
    double f, d;
    while (in >> f >> d) {
        notes.push_back(f);
        durations.push_back(d);
    }
    in.close();

    ofstream wav;
    wav.open("output.wav", ios::binary);
    if (!wav.is_open()) { cerr << "cannot open output"; return 1; }

    // header
    wav << chunk_id;
    wav << "----";              // chunk size placeholder
    wav << format;
    wav << subchunk1_id;
    write_as_bytes(wav, subchunk1_size, 4);
    write_as_bytes(wav, audio_format, 2);
    write_as_bytes(wav, num_channels, 2);
    write_as_bytes(wav, sample_rate, 4);
    write_as_bytes(wav, byte_rate, 4);
    write_as_bytes(wav, block_align, 2);
    write_as_bytes(wav, bits_per_sample, 2);
    wav << subchunk2_id;
    wav << "----";              // data size placeholder

    int start_audio = wav.tellp();

    // synthesize each note
    for (size_t n = 0; n < notes.size(); n++) {
        double freq = notes[n];
        int samples_per_note = durations[n] * sample_rate;

        for (int i = 0; i < samples_per_note; i++) {
            double val = sin((2 * 3.14 * i * freq) / sample_rate);
            double sample = val * max_amp * 0.5;

            // --- envelope: short fade in/out to remove clicks between notes.
            //     Remove this block if you want the raw (clicky) sound. ---
            int fade = 500;
            double envelope = 1.0;
            if (i < fade)
                envelope = (double)i / fade;
            else if (i > samples_per_note - fade)
                envelope = (double)(samples_per_note - i) / fade;
            sample = sample * envelope;
            // --- end envelope ---

            write_as_bytes(wav, (int)sample, 2);   // left
            write_as_bytes(wav, (int)sample, 2);   // right
        }
    }

    int end_audio = wav.tellp();
    wav.seekp(start_audio - 4);
    write_as_bytes(wav, end_audio - start_audio, 4);
    wav.seekp(4, ios::beg);
    write_as_bytes(wav, end_audio - 8, 4);
    wav.close();
    return 0;
}
