// Lane ME bench (PROPOSAL, untested: no hardware was built by the lane): four pencil-lead memistors, one per jar.
// Write: counter electrode k (pin CE[k], direct) against the lead chain (pin LEADS through ONE shared 1 kOhm); plating = lead
// negative. The write current is the drop across that 1 kOhm (A0 = LEADS pin side, A1 = chain side), integrated (coulombs).
// Read: ~18 mA from pin READ_P through 270 Ohm, through the four leads in series, back to READ_N; the CD4052 selects lead k's
// two sense wires into an INA219 (shunt input, 10 uV LSB). Each read is taken in both polarities and averaged, so the read
// current plates nothing on balance.
// Serial (115200): "P k uC" plate lead k by uC microcoulombs; "D k uC" deplate; "R k" read; "S" read all.
// Every line printed: t_ms,cmd,k,charge_uC,energy_uJ,ms,R_mOhm
#include <Wire.h>

const int CE[4] = {2, 3, 4, 5};      // counter electrodes (copper wire, one per jar), wired directly
const int LEADS = 6;                 // the lead chain's write terminal
const int READ_P = 7, READ_N = 8;    // read current pins (220 Ohm in series)
const int MUX_A = 9, MUX_B = 10;     // CD4052 address
const int SENSE_PIN = A0, CELL_PIN = A1;
const float R_WRITE = 1000.0;        // ohm
const float R_READ = 270.0;
const uint8_t INA = 0x40;

int16_t inaShunt() {                 // shunt voltage register (10 uV LSB)
  Wire.beginTransmission(INA); Wire.write(0x01); Wire.endTransmission();
  Wire.requestFrom(INA, (uint8_t)2);
  int16_t v = (Wire.read() << 8) | Wire.read();
  return v;
}

void inaInit() {                     // PGA /8 (+-320 mV), 12-bit, 128-sample average
  Wire.beginTransmission(INA); Wire.write(0x00); Wire.write(0x1F); Wire.write(0xFF); Wire.endTransmission();
}

void allHiZ() {
  for (int k = 0; k < 4; k++) pinMode(CE[k], INPUT);
  pinMode(LEADS, INPUT); pinMode(READ_P, INPUT); pinMode(READ_N, INPUT);
}

float readOhm(int k) {               // 4-wire, both polarities
  digitalWrite(MUX_A, k & 1); digitalWrite(MUX_B, (k >> 1) & 1);
  float v[2];
  for (int pol = 0; pol < 2; pol++) {
    pinMode(READ_P, OUTPUT); pinMode(READ_N, OUTPUT);
    digitalWrite(READ_P, pol ? LOW : HIGH); digitalWrite(READ_N, pol ? HIGH : LOW);
    delay(70);                       // 128-sample INA219 conversion is ~69 ms
    v[pol] = inaShunt() * 10.0;      // uV
    pinMode(READ_P, INPUT); pinMode(READ_N, INPUT);
  }
  float vs = 0.5 * (v[0] - v[1]);    // uV across the lead
  float i = 5.0 / (R_READ + 4 * 2.0) * 1e6;  // uA, nominal (calibrate with a 1 Ohm reference: BENCH.md step 3)
  return vs / i * 1000.0;            // milliohm
}

void write(int k, bool plate, float uC) {
  float q = 0, e = 0;
  unsigned long t0 = millis(), last = micros();
  pinMode(CE[k], OUTPUT); pinMode(LEADS, OUTPUT);
  digitalWrite(CE[k], plate ? HIGH : LOW); digitalWrite(LEADS, plate ? LOW : HIGH);
  while (q < uC) {
    float va = analogRead(SENSE_PIN) * (5.0 / 1023.0);
    float vb = analogRead(CELL_PIN) * (5.0 / 1023.0);
    unsigned long now = micros();
    float dt = (now - last) * 1e-6; last = now;
    float i = fabs(va - vb) / R_WRITE;         // A
    float vcell = plate ? (5.0 - vb) : vb;     // cell voltage: CE at 5 V (plate) or 0 V (deplate), chain at A1
    q += i * dt * 1e6; e += i * vcell * dt * 1e6;
    if (millis() - t0 > 20000) break;          // safety stop
  }
  allHiZ();
  Serial.print(millis()); Serial.print(plate ? ",P," : ",D,"); Serial.print(k); Serial.print(',');
  Serial.print(q, 1); Serial.print(','); Serial.print(e, 2); Serial.print(','); Serial.print(millis() - t0);
  Serial.print(','); Serial.println(readOhm(k), 2);
}

void setup() {
  Serial.begin(115200); Wire.begin(); inaInit();
  pinMode(MUX_A, OUTPUT); pinMode(MUX_B, OUTPUT); allHiZ();
  Serial.println("t_ms,cmd,k,charge_uC,energy_uJ,ms,R_mOhm");
}

void loop() {
  if (!Serial.available()) return;
  char c = Serial.read();
  if (c == 'P' || c == 'D') {
    int k = Serial.parseInt(); float uC = Serial.parseFloat();
    if (k >= 0 && k < 4 && uC > 0 && uC < 100000) write(k, c == 'P', uC);
  } else if (c == 'R') {
    int k = Serial.parseInt();
    Serial.print(millis()); Serial.print(",R,"); Serial.print(k); Serial.print(",0,0,0,"); Serial.println(readOhm(k), 2);
  } else if (c == 'S') {
    for (int k = 0; k < 4; k++) {
      Serial.print(millis()); Serial.print(",R,"); Serial.print(k); Serial.print(",0,0,0,"); Serial.println(readOhm(k), 2);
    }
  }
}
